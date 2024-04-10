classdef BlueFTController
    properties
        ip
        key
        port
        mixing_chamber_channel_id
        mixing_chamber_heater
        debug
        logger
    end

    methods
        function obj = BlueFTController(ip, mixing_chamber_channel_id, port, key, debug)
            if nargin < 5
                debug = false;
            end
            obj.ip = ip;
            obj.mixing_chamber_channel_id = mixing_chamber_channel_id;
            obj.port = port;
            obj.key = key;
            obj.debug = debug;
            obj.setupLogging();
        end

        function setupLogging(obj)
            obj.logger = Logger();
            if obj.debug
                obj.logger.setLogLevel('DEBUG');
            else
                obj.logger.setLogLevel('INFO');
            end
        end

        function value = getValueFromDataResponse(obj, data, device, target)
            try
                if ~obj.getSynchronizationStatus(data, device, target)
                    warning('The obtained value is not synchronized!');
                end
                value = data.data.(device).(target).latest_valid_value.value;
            catch
                warning('Could not verify synchronization status');
                value = false;
            end
        end

        function synchronized = getSynchronizationStatus(obj, data, device, target)
            try
                synchronized = strcmp(data.data.(device).(target).latest_valid_value.status, 'SYNCHRONIZED');
            catch
                warning('Could not verify synchronization status');
                synchronized = false;
            end
        end

        function response = getValueRequest(obj, device, target)
            if isempty(obj.key)
                error('No key provided for value request.');
            end
            requestPath = sprintf('https://%s:%d/values/%s/%s/?prettyprint=1&key=%s', obj.ip, obj.port, strrep(device, '.', '/'), target, obj.key);
            obj.logger.debug(sprintf('GET: %s', requestPath));
            try
                response = webread(requestPath);
            catch exception
                obj.logger.error(sprintf('Error: %s', exception.message));
                response.data.content.latest_valid_value.value = nan;
                response.data.content.latest_valid_value.status = 'ERROR';
            end
        end

        function response = setValueRequest(obj, device, target, value)
            if isempty(obj.key)
                error('No key provided for value request.');
            end
            request_body = struct('data', struct(strcat(device, '.', target), struct('content', struct('value', value))));
            requestPath = sprintf('https://%s:%d/values/?prettyprint=1&key=%s', obj.ip, obj.port, obj.key);
            obj.logger.debug(sprintf('POST: %s - Body: %s', requestPath, jsonencode(request_body)));
            options = weboptions('RequestMethod', 'post', 'MediaType', 'application/json', 'ContentType', 'json', 'CertificateFilename', '');
            try
                response = webwrite(requestPath, request_body, options);
            catch exception
                obj.logger.error(sprintf('Error: %s', exception.message));
                response.data.content.latest_valid_value.value = nan;
                response.data.content.latest_valid_value.status = 'ERROR';
            end
        end

        function response = applyValuesRequest(obj, device)
            if isempty(obj.key)
                error('No key provided for value request.');
            end
            request_body = struct('data', struct(strcat(device, '.write'), struct('content', struct('call', 1))));
            requestPath = sprintf('https://%s:%d/values/?prettyprint=1&key=%s', obj.ip, obj.port, obj.key);
            obj.logger.debug(sprintf('POST: %s - Body: %s', requestPath, jsonencode(request_body)));
            options = weboptions('RequestMethod', 'post', 'MediaType', 'application/json', 'ContentType', 'json', 'CertificateFilename', '');
            try
                response = webwrite(requestPath, request_body, options);
            catch exception
                obj.logger.error(sprintf('Error: %s', exception.message));
                response.data.content.latest_valid_value.value = nan;
                response.data.content.latest_valid_value.status = 'ERROR';
            end
        end

        function value = getChannelData(obj, channel, target_value)
            device_id = sprintf('mapper.heater_mappings_bftc.device.c%d', channel);
            obj.logger.info(sprintf('Requesting value: %s from channel %d', target_value, channel));
            data = obj.getValueRequest(device_id, target_value);
            try
                value = obj.getValueFromDataResponse(data, device_id, target_value);
            catch
                response.error = data;
                error('APIError', jsonencode(response));
            end
        end

        function temperature = getChannelTemperature(obj, channel)
            temperature = obj.getChannelData(channel, 'temperature');
        end

        function resistance = getChannelResistance(obj, channel)
            resistance = obj.getChannelData(channel, 'resistance');
        end

        function temperature = getMxcTemperature(obj)
            temperature = obj.getChannelTemperature(obj.mixing_chamber_channel_id);
        end

        function resistance = getMxcResistance(obj)
            resistance = obj.getChannelResistance(obj.mixing_chamber_channel_id);
        end

        function heater_value = getMxcHeaterValue(obj, target)
            data = obj.getValueRequest(obj.mixing_chamber_heater, target);
            try
                heater_value = obj.getValueFromDataResponse(data, obj.mixing_chamber_heater, target);
            catch
                response.error = data;
                error('APIError', jsonencode(response));
            end
        end

        function synchronized = checkHeaterValueSynced(obj, target)
            data = obj.getValueRequest(obj.mixing_chamber_heater, target);
            try
                synchronized = obj.getSynchronizationStatus(data, obj.mixing_chamber_heater, target);
            catch
                response.error = data;
                error('APIError', jsonencode(response));
            end
        end

        function setMxcHeaterValue(obj, target, value)
            obj.logger.info(sprintf('Mixing Chamber Heater: Setting %s to %f', target, value));
            obj.setValueRequest(obj.mixing_chamber_heater, target, value);
            obj.logger.info('Mixing Chamber Heater: Applying settings');
            obj.applyValuesRequest(obj.mixing_chamber_heater);
            synchronized = obj.checkHeaterValueSynced(target);
            obj.logger.info('Mixing Chamber Heater: Settings applied and synced');
        end

        function status = getMxcHeaterStatus(obj)
            status = obj.getMxcHeaterValue('active') == '1';
        end

        function success = setMxcHeaterStatus(obj, newStatus)
            newValue = '1' if newStatus else '0';
            success = obj.setMxcHeaterValue('active', newValue);
        end

        function success = toggleMxcHeater(obj, status)
            if strcmp(status, 'on')
                newValue = true;
            elseif strcmp(status, 'off')
                newValue = false;
            else
                error('PIDConfigException', 'Invalid status provided, must be ''on'' or ''off''');
            end
            success = obj.setMxcHeaterValue(newValue);
        end

        function power = getMxcHeaterPower(obj)
            power = obj.getMxcHeaterValue('power') * 1e6;
        end

        function success = setMxcHeaterPower(obj, power)
            if power < 0 || power > 1000
                error('PIDConfigException', 'Power should be in the range of 0 to 1000 microwatts');
            end
            success = obj.setMxcHeaterValue('power', power / 1e6);
        end

        function setpoint = getMxcHeaterSetpoint(obj)
            setpoint = obj.getMxcHeaterValue('setpoint');
        end

        function success = setMxcHeaterSetpoint(obj, temperature)
            success = obj.setMxcHeaterValue('setpoint', temperature / 1e3);
        end

        function mode = getMxcHeaterMode(obj)
            mode = obj.getMxcHeaterValue('pid_mode') == '1';
        end

        function success = setMxcHeaterMode(obj, toggle)
            newValue = '1' if toggle else '0';
            success = obj.setMxcHeaterValue('pid_mode', newValue);
        end
    end
end
