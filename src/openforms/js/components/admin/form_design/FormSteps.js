import React, {useState} from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import {FormattedMessage} from 'react-intl';

import ValidationErrorsProvider from 'components/admin/forms/ValidationErrors';
import Loader from 'components/admin/Loader';

import FormStep from './FormStep';
import FormStepsNav from './FormStepsNav';

const FormSteps = ({
  steps = [],
  onEdit,
  onComponentMutated,
  onFieldChange,
  onLiteralFieldChange,
  onDelete,
  onReorder,
  onReplace,
  onAdd,
  languages,
  submitting = false,
}) => {
  const [activeStepIndex, setActiveStepIndex] = useState(steps.length ? 0 : null);
  const activeStep = steps.length ? steps[activeStepIndex] : null;

  const className = classNames('edit-panel', {'edit-panel--submitting': submitting});

  return (
    <section className={className}>
      {submitting ? (
        <div className="edit-panel__submit-layer">
          <Loader />
        </div>
      ) : null}
      <div className="edit-panel__nav">
        <FormStepsNav
          steps={steps}
          active={activeStep}
          onActivateStep={setActiveStepIndex}
          onReorder={onReorder}
          onDelete={onDelete}
          onAdd={onAdd}
        />
      </div>
      <div className="edit-panel__edit-area">
        {activeStep ? (
          <ValidationErrorsProvider errors={activeStep.validationErrors}>
            <FormStep
              data={activeStep}
              onEdit={onEdit.bind(null, activeStepIndex)}
              onComponentMutated={onComponentMutated}
              onFieldChange={onFieldChange.bind(null, activeStepIndex)}
              onLiteralFieldChange={onLiteralFieldChange.bind(null, activeStepIndex)}
              onReplace={onReplace.bind(null, activeStepIndex)}
              languages={languages}
            />
          </ValidationErrorsProvider>
        ) : (
          <FormattedMessage
            defaultMessage="Select a step to view or modify."
            description="No-active-step-selected notice"
          />
        )}
      </div>
    </section>
  );
};

FormSteps.propTypes = {
  steps: PropTypes.arrayOf(
    PropTypes.shape({
      configuration: PropTypes.object,
      formDefinition: PropTypes.string,
      index: PropTypes.number,
      name: PropTypes.string,
      slug: PropTypes.string,
      url: PropTypes.string,
      isNew: PropTypes.bool,
      validationErrors: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
    })
  ),
  onEdit: PropTypes.func.isRequired,
  onComponentMutated: PropTypes.func.isRequired,
  onFieldChange: PropTypes.func.isRequired,
  onLiteralFieldChange: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onReorder: PropTypes.func.isRequired,
  onReplace: PropTypes.func.isRequired,
  onAdd: PropTypes.func.isRequired,
  languages: PropTypes.array,
  submitting: PropTypes.bool,
};

export default FormSteps;
