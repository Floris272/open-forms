import {Formio} from 'formiojs';

import DEFAULT_TABS, {ADVANCED, BASIC, REGISTRATION, TRANSLATIONS, VALIDATION} from './edit/tabs';
import {localiseSchema} from './i18n';

const Select = Formio.Components.components.select;

const values = [
  {
    type: 'datagrid',
    input: true,
    label: 'Values',
    key: 'data.values',
    tooltip:
      'The radio button values that can be picked for this field. Values are text submitted with the form data. Labels are text that appears next to the radio buttons on the form.',
    weight: 10,
    reorder: true,
    defaultValue: [{label: '', value: ''}],
    components: [
      {
        label: 'Label',
        key: 'label',
        input: true,
        type: 'textfield',
      },
      {
        label: 'Value',
        key: 'value',
        input: true,
        type: 'textfield',
        allowCalculateOverride: true,
        calculateValue: {_camelCase: [{var: 'row.label'}]},
      },
    ],
  },
];

class SelectField extends Select {
  static schema(...extend) {
    return localiseSchema({...Select.schema(...extend), key: 'select-key'});
  }

  static get builderInfo() {
    return {
      ...Select.builderInfo,
      schema: SelectField.schema(),
    };
  }

  static editForm() {
    const BASIC_TAB = {
      ...BASIC,
      components: [...BASIC.components, ...values],
    };
    const TABS = {
      ...DEFAULT_TABS,
      components: [BASIC_TAB, ADVANCED, VALIDATION, REGISTRATION, TRANSLATIONS],
    };
    return {components: [TABS]};
  }
}

export default SelectField;
