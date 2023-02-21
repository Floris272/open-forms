import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import FAIcon from 'components/admin/FAIcon';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';

import {FormLogicContext} from './../Context';
import ServiceFetchConfigurationForm from './ServiceFetchConfigurationForm';

const ServiceFetchConfigurationPicker = ({data = {}, onChange, onFormSave}) => {
  const intl = useIntl();
  const formLogicContext = useContext(FormLogicContext);

  const [selectExisting, setSelectExisting] = useState(false);
  const [selectedServiceFetchConfig, setselectedServiceFetchConfig] = useState(null);
  const [showServiceFetchConfigurationForm, setShowServiceFetchConfigurationForm] = useState(false);
  const [serviceFetchData, setServiceFetchData] = useState({});

  const serviceFetchConfigurationChoices = formLogicContext.serviceFetchConfigurations.map(
    fetchConfig => {
      return [
        fetchConfig.url,
        `${fetchConfig.method} ${fetchConfig.path} (${fetchConfig.service})`,
      ];
    }
  );

  return (
    <div className="servicefetchconfiguration-picker">
      <div className="tiles tiles--horizontal">
        <button type="button" className="tiles__tile" onClick={() => setSelectExisting(true)}>
          <FAIcon
            icon="recycle"
            extraClassname="fa-2x"
            title={intl.formatMessage({
              description: 'select service fetch configuration icon title',
              defaultMessage: 'Select service fetch configuration',
            })}
          />
          <span>
            <FormattedMessage
              description="Select existing service fetch configuration tile"
              defaultMessage="Select existing service fetch configuration"
            />
          </span>
        </button>

        <span className="tiles__separator">&bull;</span>

        <button
          type="button"
          className="tiles__tile"
          onClick={() => {
            setSelectExisting(false);
            setShowServiceFetchConfigurationForm(true);
          }}
        >
          <FAIcon
            icon="pen-to-square"
            extraClassname="fa-2x"
            title={intl.formatMessage({
              description: 'create service fetch configuration icon title',
              defaultMessage: 'Create service fetch configuration',
            })}
          />
          <span>
            <FormattedMessage
              description="Create service fetch configuration tile"
              defaultMessage="Create a new service fetch configuration"
            />
          </span>
        </button>
      </div>

      {selectExisting ? (
        <div className="servicefetchconfiguration-select">
          <FormRow>
            <Field
              name={'fetchConfiguration.existing'}
              label={
                <FormattedMessage
                  defaultMessage="Choose service fetch configuration"
                  description="Service fetch configuration modal select existing field label"
                />
              }
            >
              <Select
                name="fetchConfiguration.existing"
                choices={serviceFetchConfigurationChoices}
                value={selectedServiceFetchConfig}
                onChange={event => {
                  // TODO ensure this onChange sets the state config data to the values of
                  // the selected config
                  onChange(event);
                  setselectedServiceFetchConfig(event.target.value);
                  setServiceFetchData(
                    formLogicContext.serviceFetchConfigurations.find(
                      element => element.url === event.target.value
                    )
                  );
                  setShowServiceFetchConfigurationForm(true);
                }}
                allowBlank
              />
            </Field>
          </FormRow>
        </div>
      ) : null}

      {showServiceFetchConfigurationForm ? (
        <div className="servicefetchconfiguration-form">
          <ServiceFetchConfigurationForm
            stateData={serviceFetchData}
            setData={setServiceFetchData}
            selectExisting={selectExisting}
            onFormSave={onFormSave}
            onChange={onChange}
          />
        </div>
      ) : null}
    </div>
  );
};

ServiceFetchConfigurationPicker.propTypes = {
  onReplace: PropTypes.func.isRequired,
};

export default ServiceFetchConfigurationPicker;
