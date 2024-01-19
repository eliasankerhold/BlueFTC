classdef BlueForsTempControl
    properties 
        ip
        port 
        httpiport
        channels
        heaters
        default_weboptions
        time_difference
    end
    methods
        % constructor
        % ip: LAN IP of temperature controller
        % delta_t: time difference between local device time and computer
        % time
        function obj = BlueForsTempControl(ip, delta_t)
            obj.ip = ip;
            obj.port = '5001';
            obj.httpiport = strcat('http://', obj.ip, ':',obj.port);
            obj.default_weboptions = weboptions('MediaType', 'application/json');
            obj.time_difference = delta_t;
        end
        
        % adds channels (i.e. temperature sensors) and automatically
        % retrieves their names
        % varargin: indices of used temperature channels
        function obj = add_channels(obj, varargin)
            local_channels = struct;
            path = obj.make_endpoint(obj.httpiport, 'channel');
            for i = 1:length(varargin)
                local_channels(i).in_use = false;
                payload.channel_nr = varargin{i};
                ch_info = obj.generic_request_legacy(path, payload);
                local_channels(varargin{i}).number = ch_info.channel_nr;
                local_channels(varargin{i}).name = ch_info.name;
                local_channels(varargin{i}).in_use = true;
            end
            obj.channels = local_channels;
        end

        % internal function, changes channels property
        function obj = set.channels(obj, new_channels)
            obj.channels = new_channels;
        end
        
        % adds heaters and automatically retrieves their names
        % varargin: indices of used heaters
        function obj = add_heaters(obj, varargin)
            local_heaters = struct;
            path = obj.make_endpoint(obj.httpiport, 'heater');
            for i = 1:length(varargin)
                local_heaters(i).in_use = false;
                payload.heater_nr = varargin{i};
                heater_info = obj.generic_request_legacy(path, payload);
                local_heaters(varargin{i}).name = heater_info.name;
                local_heaters(varargin{i}).number = heater_info.heater_nr;
                local_heaters(varargin{i}).in_use = true;
            end
            obj.heaters = local_heaters;
        end
        
        % internal function, changes heaters property
        function obj = set.heaters(obj, new_heaters)
            obj.heaters = new_heaters;
        end
        
        % could not be tested yet since no errors occured!
        % generic error handling class, should abort execution and display
        % the error. See API Manual for explanation of error codes.
        % response: return value of webwrite function call
        function generic_error_handler(obj, response)
            if strcmpi(response.status, 'error')
                disp(response.error);
                error('BLUEFORS device error!')
            end
        end
            

        % internal tool to easily create required endpoint paths
        % vargargin: arbritary number of strings
        % returns: ready to use endpoint path as string
        function string = make_endpoint(varargin)
            string = '';
            for i = 2:length(varargin)
                if i < length(varargin)
                    string = strcat(string, varargin{i}, '/');
                else
                    string = strcat(string, varargin{i});
                end
            end
        end
        
        % handles generic HTTP POST request, listens to errors and returns
        % response object. Takes exactly 2 or 3 arguments.
        % path: endpoint path created using make_endpoint
        % varargin (optional): payload struct
        function answerstruct = generic_request_legacy(obj, path, varargin)
            disp(obj.default_weboptions)
            disp(path)
            if nargin == 2
                answerstruct = webread(path);
            elseif nargin == 3
                answerstruct = webwrite(path, varargin{1}, ...
                    obj.default_weboptions);
            else
                error('Incorrect number of arguments!')
            end           
            obj.generic_error_handler(answerstruct)
        end

        % turns channel on or off
        % channel_nr: number of channel
        % status: either 'on' or 'off'
        function toggle_channel(obj, channel_nr, status)
            if channel_nr > length(obj.channels) || ~obj.channels(channel_nr).in_use
                warning(['You are activating/deactivating a channel that ' ...
                    'has not been initialized. Even though this will work, ' ...
                    'it is strongly advised to initialize all channels ' ...
                    'using the add_channels method!'])
            end
            if strcmpi(status, 'on')
                tog = true;
            elseif strcmpi(status, 'off')
                tog = false;
            else
                error('Wrong status! Use on or off.')
            end
            path = obj.make_endpoint('channel', 'update');
            payload.channel_nr = channel_nr;
            payload.active = tog;
            obj.generic_request_legacy(path, payload)
            fprintf('Turned channel %i %s.\n', channel_nr, setstatus);
        end
        
        % gets the latest temperature measurements of all registered
        % channels by requesting all historical data measured during the
        % last 200 seconds. This time interval might have to be adjusted to
        % the measurement time set on the device. In future versions, the
        % measurement time will be read automatically and the time interval
        % adjusted accordingly. Reference API chapter 2.9 for more info.
        % returns: struct with temperature info, channel name and timestamp
        function temps = get_latest_temps(obj)
            path = obj.make_endpoint(obj.httpiport, 'channel', ...
                'historical-data');
            payload.start_time = obj.make_past_timestr(200);
            payload.stop_time = obj.make_timestr(now);
            for i = 1:length(obj.channels)
                if ~obj.channels(i).in_use
                    continue
                end
                payload.channel_nr = obj.channels(i).number;
                payload.fields = {'temperature', 'timestamp'};
                meas = obj.generic_request_legacy(path, payload);
                temps(i).name = obj.channels(i).name;
                d = datestr(datetime(meas.measurements.timestamp(end), ...
                    'convertfrom', 'posixtime', 'Format', ...
                    'MM/dd/yy HH:mm:ss.SSS'), 'yyyy-mm-dd:HH:MM:SS.FFF');
                temps(i).timestamp = d;
                temps(i).temp = meas.measurements.temperature(end);
            end
        end
        
        % gets all temperature values of a specific channel measurement in
        % the last XX seconds
        % channel_number: number of channel
        % time_seconds: length of time interval in seconds
        % returns: struct with temperatures and timestamps
        function temps = get_channel_temps_in_time(obj, channel_number, time_seconds)
            path = obj.make_endpoint(obj.httpiport, 'channel', ...
                    'historical-data');
            payload.start_time = obj.make_past_timestr(time_seconds);
            payload.stop_time = obj.make_timestr(now);
            payload.channel_nr = channel_number;
            payload.fields = {'temperature', 'timestamp'};
            meas = obj.generic_request_legacy(path, payload);
            d = datestr(datetime(meas.measurements.timestamp, ...
                    'convertfrom', 'posixtime', 'Format', ...
                    'MM/dd/yy HH:mm:ss.SSS'), 'yyyy-mm-dd:HH:MM:SS.FFF');
            temps.temperature = meas.measurements.temperature;
            temps.timestamp = d;
        end
        
        % turns heater on or off
        % heater_index: number of heater
        % status: either 'on' or 'off' (case insensitive)
        function toggle_heater(obj, heater_index, setstatus)
            if heater_index > length(obj.heaters) || ~obj.heaters(heater_index).in_use
                warning(['You are activating/deactivating a heater that ' ...
                    'has not been initialized. Even though this will work, ' ...
                    'it is strongly advised to initialize all heaters ' ...
                    'using the add_heaters method!'])
            end
            if strcmpi(setstatus, 'on')
                tog = true;
            elseif strcmpi(setstatus, 'off')
                tog = false;
            else
                error('Wrong status! Use on or off.')
            end
            
            path = obj.make_endpoint(obj.httpiport, 'heater', 'update');
            payload.heater_nr = heater_index;
            payload.active = tog;
            obj.generic_request_legacy(path, payload);
            fprintf('Turned heater %i %s.\n', heater_index, setstatus);
        end
           
        % sets specific power to heater
        % heater_index: number of heater
        % power: power in uW (microwatts, 1e-6 W)
        function set_heater_power(obj, heater_index, setpower)
            if obj.get_pid_mode(heater_index) == 1
                warning('Cannot set manual power since heater %i is in pid mode.\n', heater_index)
                return;
            end
            
            path = obj.make_endpoint(obj.httpiport, 'heater', 'update');
            power_in_watts = setpower * 1e-6;
            payload.heater_nr = heater_index;
            payload.power = power_in_watts;
            obj.generic_request_legacy(path, payload);
            fprintf('Set heater %i to %f uW.\n', heater_index, setpower)
        end
        
        % reads current heater power
        % heater_index: number of heater
        % returns: power in uW (microwatts, 1e-6 W)
        function power = get_heater_power(obj, heater_index)
            path = obj.make_endpoint(obj.httpiport, 'heater');
            payload.heater_nr = heater_index;
            answer = obj.generic_request_legacy(path, payload);
            power = answer.power * 1e6;
        end
        
        % reads current pid mode of heater
        % heater_index: number of heater
        % returns: 0 for manual mode, 1 for pid mode       
        function mode = get_pid_mode(obj, heater_index)
            path = obj.make_endpoint(obj.httpiport, 'heater');
            payload.heater_nr = heater_index;
            answer = obj.generic_request_legacy(path, payload);
            mode = answer.pid_mode;
        end

        % toggles manual and pid mode 
        % heater_index: number of heater
        % setstatus: either 'manual' or 'pid' (case insensitive)
        function toggle_pid_mode(obj, heater_index, setstatus)
            if heater_index > length(obj.heaters) || ~obj.heaters(heater_index).in_use
                warning(['You are changing the pid status of a heater that ' ...
                    'has not been initialized. Even though this will work, ' ...
                    'it is strongly advised to initialize all heaters ' ...
                    'using the add_heaters method!'])
            end
            if strcmpi(setstatus, 'manual') 
                if obj.get_pid_mode(heater_index) == 0
                    warning('Heater %i already is in %s mode.\n', heater_index, setstatus)
                    return;
                end
                tog = 0;
            elseif strcmpi(setstatus, 'pid')
                if obj.get_pid_mode(heater_index) == 1
                    warning('Heater %i already is in %s mode.\n', heater_index, setstatus)
                    return;
                end
                tog = 1;
            else
                error('Wrong status! Use on or off.')
            end

            path = obj.make_endpoint(obj.httpiport, 'heater', 'update');
            payload.heater_nr = heater_index;
            payload.pid_mode = tog;
            obj.generic_request_legacy(path, payload);
            fprintf('Turned heater %i to %s mode.\n', heater_index, setstatus);            
        end

        % changes the pid parameters of a heater
        % heater_index: heater number
        % prop: pid parameter proportional
        % int: pid parameter integral
        % dev: pid parameter derivative
        function set_pid_parameters(obj, heater_index, prop, int, dev)
            if heater_index > length(obj.heaters) || ~obj.heaters(heater_index).in_use
                warning(['You are changing the pid settings of a heater that ' ...
                    'has not been initialized. Even though this will work, ' ...
                    'it is strongly advised to initialize all heaters ' ...
                    'using the add_heaters method!'])
            end
            
            path = obj.make_endpoint(obj.httpiport, 'heater', 'update');
            payload.heater_nr = heater_index;
            payload.control_algorithm_settings.proportional = prop;
            payload.control_algorithm_settings.integral = int;
            payload.control_algorithm_setting.derivative = dev;
            obj.generic_request_legacy(path, payload);
            fprintf(['Set pid paramaters of heater %i to proportional: %s,'...
                'intergral: %s, derivative: %s.\n'], heater_index, prop, int, dev);
        end

        % sets a target_temperature (setpoint) for the pid control
        % heater_index: heater number
        % target_temp: target temperature in mK (milikelvin, 1e-3)
        function set_target_temperature(obj, heater_index, target_temp)
            if heater_index > length(obj.heaters) || ~obj.heaters(heater_index).in_use
                warning(['You are changing the target temperature of a heater that ' ...
                    'has not been initialized. Even though this will work, ' ...
                    'it is strongly advised to initialize all heaters ' ...
                    'using the add_heaters method!'])
            end
            
            if obj.get_pid_mode(heater_index) == 0
                fprintf('Heater %i is in manual mode. Target temperature will still be set.\n', heater_index)
            end
            
            path = obj.make_endpoint(obj.httpiport, 'heater', 'update');
            payload.heater_nr = heater_index;
            payload.setpoint = target_temp * 1e-3;
            obj.generic_request_legacy(path, payload);
            fprintf('Set target temperature of pid for heater %i to %f mK.\n', ...
                heater_index, target_temp);
        end
   
        % internal function used to format timestrings
        function timestr = make_timestr(obj, t)
            t = t - seconds(obj.time_difference);
            date = datestr(t, 'yyyy-mm-dd');
            time = datestr(t, 'HH:MM:SS');
            timestr = strcat(date, 'T', time, 'Z');
        end

        % internal function used to make delayed timestamp
        function timestr = make_past_timestr(obj, delta_seconds)
            timestr = obj.make_timestr(now - seconds(delta_seconds));
        end
    end
end


