from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, TypedDict

from glom import assign
from json_logic import jsonLogic
from typing_extensions import Self

from openforms.dmn.service import evaluate_dmn
from openforms.formio.datastructures import FormioData
from openforms.formio.service import FormioConfigurationWrapper
from openforms.forms.constants import LogicActionTypes
from openforms.forms.models import FormLogic, FormVariable
from openforms.typing import DataMapping, JSONObject
from openforms.variables.models import ServiceFetchConfiguration

from ..models import Submission, SubmissionStep
from ..models.submission_step import DirtyData
from .log_utils import log_errors
from .service_fetching import perform_service_fetch


class ActionDetails(TypedDict):
    type: str
    property: dict
    state: Any
    value: Any
    config: dict


class ActionDict(TypedDict):
    component: str
    variable: str
    form_step: str
    form_step_uuid: str
    action: ActionDetails


def compile_action_operation(action: ActionDict) -> ActionOperation:
    action_type = action["action"]["type"]
    cls = ACTION_TYPE_MAPPING[action_type]
    return cls.from_action(action)


class ActionOperation:
    rule: FormLogic

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        """
        Constructor from an ActionDict
        """
        pass

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        """
        Implements the side effects of the action operation.
        """
        pass

    def eval(
        self,
        context: DataMapping,
        submission: Submission,
    ) -> DataMapping | None:
        """
        Return a mapping [name/path -> new_value] with changes that are to be
        applied to the context.
        """
        pass


@dataclass
class PropertyAction(ActionOperation):
    component: str
    property: str
    value: Any

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(
            component=action["component"],
            property=action["action"]["property"]["value"],
            value=action["action"]["state"],
        )

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        if self.component not in configuration:
            return None
        component = configuration[self.component]
        assign(component, self.property, self.value, missing=dict)


class DisableNextAction(ActionOperation):
    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls()

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        step._can_submit = False


@dataclass
class StepNotApplicableAction(ActionOperation):
    form_step_identifier: str

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(
            form_step_identifier=action["form_step_uuid"],
        )

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        execution_state = (
            step.submission.load_execution_state()
        )  # typically cached already
        submission_step_to_modify = execution_state.resolve_step(
            self.form_step_identifier
        )
        submission_step_to_modify.is_applicable = False

        # This clears data in the database to make sure that saved steps which later become
        # not-applicable don't have old data
        submission_step_to_modify.data = {}
        if submission_step_to_modify == step:
            step.is_applicable = False
            step.data = DirtyData({})


@dataclass
class StepApplicableAction(ActionOperation):
    form_step_identifier: str

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(
            form_step_identifier=action["form_step_uuid"],
        )

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        execution_state = (
            step.submission.load_execution_state()
        )  # typically cached already
        submission_step_to_modify = execution_state.resolve_step(
            self.form_step_identifier
        )
        submission_step_to_modify.is_applicable = True


@dataclass
class VariableAction(ActionOperation):
    variable: str
    value: JSONObject

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(variable=action["variable"], value=action["action"]["value"])

    def eval(
        self,
        context: DataMapping,
        submission: Submission,
    ) -> DataMapping:
        with log_errors(self.value, self.rule):
            return {self.variable: jsonLogic(self.value, context)}


@dataclass
class ServiceFetchAction(ActionOperation):
    variable: str
    fetch_config: int

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(variable=action["variable"], fetch_config=action["action"]["value"])

    def eval(
        self,
        context: DataMapping,
        submission: Submission,
    ) -> DataMapping:
        # FIXME
        # https://github.com/open-formulieren/open-forms/issues/3052
        if self.fetch_config:  # the old way
            var = FormVariable(
                key=self.variable,
                service_fetch_configuration=ServiceFetchConfiguration.objects.get(
                    pk=self.fetch_config
                ),
            )
        else:  # the current way
            var = self.rule.form.formvariable_set.get(key=self.variable)
        with log_errors({}, self.rule):  # TODO proper error handling
            result = perform_service_fetch(var, context, str(submission.uuid))
            return {var.key: result.value}


class DMNVariableMapping(TypedDict):
    form_variable: str
    dmn_variable: str


class DMNConfig(TypedDict):
    plugin_id: str
    input_mapping: list[DMNVariableMapping]
    output_mapping: list[DMNVariableMapping]
    decision_definition_id: str
    decision_definition_version: str


@dataclass
class EvaluateDMNAction(ActionOperation):
    input_mapping: list[DMNVariableMapping]
    output_mapping: list[DMNVariableMapping]
    decision_definition_id: str
    plugin_id: str
    decision_definition_version: str = ""

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        dmn_config: DMNConfig = action["action"]["config"]

        return cls(**dmn_config)

    def eval(
        self,
        context: DataMapping,
        submission: Submission,
    ) -> DataMapping | None:
        # Mapping from form variables to DMN inputs
        data = FormioData(context)
        dmn_inputs = {
            item["dmn_variable"]: data[item["form_variable"]]
            for item in self.input_mapping
        }

        # Perform DMN call
        dmn_outputs = evaluate_dmn(
            definition_id=self.decision_definition_id,
            version=self.decision_definition_version,
            input_values=dmn_inputs,
            plugin_id=self.plugin_id,
        )

        # Map DMN output to form variables
        return {
            item["form_variable"]: dmn_outputs[item["dmn_variable"]]
            for item in self.output_mapping
            if item["dmn_variable"] in dmn_outputs
        }


@dataclass
class SetRegistrationBackendAction(ActionOperation):
    registration_backend_key: str

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(registration_backend_key=action["action"]["value"])

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        step.submission.finalised_registration_backend_key = (
            self.registration_backend_key
        )


ACTION_TYPE_MAPPING: Mapping[LogicActionTypes, type[ActionOperation]] = {
    LogicActionTypes.property: PropertyAction,
    LogicActionTypes.disable_next: DisableNextAction,
    LogicActionTypes.step_not_applicable: StepNotApplicableAction,
    LogicActionTypes.step_applicable: StepApplicableAction,
    LogicActionTypes.variable: VariableAction,
    LogicActionTypes.fetch_from_service: ServiceFetchAction,
    LogicActionTypes.evaluate_dmn: EvaluateDMNAction,
    LogicActionTypes.set_registration_backend: SetRegistrationBackendAction,
}
