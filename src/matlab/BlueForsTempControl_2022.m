classdef BlueForsTempControl_2022 < handle
    properties 
        ip
        port 
        httpiport
        channels
        heaters
        time_difference
        pid_ranges
        cycle_time
    end
    methods
        % constructor
        % ip: LAN IP of temperature controller
        % delta_t: time difference between local device time and computer
        % time
        % channels_in_use: number of temperature channels used, i.e. 
        % cycled through during measurement
        function obj = BlueForsTempControl_2022(ip, channels_in_use)
            obj.ip = ip;
            obj.port = '5001';
            obj.httpiport = strcat('http://', obj.ip, ':',obj.port);
            obj.cycle_time = obj.get_meas_cycle_time(channels_in_use);
            obj.time_difference = seconds(datetime("now") - ...
                obj.get_system_time);
        end

        function time = get_meas_cycle_time(obj, channels_in_use)
            path = obj.make_endpoint(obj.httpiport, 'statemachine');
            state_info = obj.generic_request(path);
            time = channels_in_use * ...
                (state_info.wait_time + state_info.meas_time);
        end

        function time_stamp = get_system_time(obj)
            path = obj.make_endpoint(obj.httpiport, 'system');
            info = obj.generic_request(path);
            time_stamp = datetime(info.datetime, 'InputFormat', ...
                'yyyy-MM-dd''T''HH:mm:ss.SSSSSS''Z');
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
                ch_info = obj.generic_request(path, payload);
                local_channels(varargin{i}).number = ch_info.channel_nr;
                local_channels(varargin{i}).name = ch_info.name;
                local_channels(varargin{i}).in_use = true;
            end
            obj.channels = local_channels;
        end
        
        % adds heaters and automatically retrieves their names
        % varargin: indices of used heaters
        function obj = add_heaters(obj, varargin)
            local_heaters = struct;
            path = obj.make_endpoint(obj.httpiport, 'heater');
            for i = 1:length(varargin)
                local_heaters(i).in_use = false;
                payload.heater_nr = varargin{i};
                heater_info = obj.generic_request(path, payload);
                local_heaters(varargin{i}).name = heater_info.name;
                local_heaters(varargin{i}).number = heater_info.heater_nr;
                local_heaters(varargin{i}).in_use = true;
            end
            obj.heaters = local_heaters;
        end
        
        % could not be tested yet since no errors occured!
        % generic error handling class for BlueFors errors, 
        % should abort execution and display
        % the error. See API Manual page 7 for explanation of error codes.
        % response: return value of webwrite function call
        function generic_bluefors_error_handler(obj, response)
            if strcmpi(response.status, 'error')
                disp(response);
                error('BLUEFORS device error!')
            end
        end

        function initialized_checker(obj, type, ind)
            if strcmpi(type, 'h')
                if ind > length(obj.heaters) || ~obj.heaters(ind).in_use
                warning(['You are accessing a heater that ' ...
                    'has not been initialized. Even though this will work, ' ...
                    'it is strongly advised to initialize all heaters ' ...
                    'using the add_heaters method!'])
                end
            elseif strcmpi(type, 'c')
                if ind > length(obj.channels) || ~obj.channels(ind).in_use
                warning(['You are accessing a channel that ' ...
                    'has not been initialized. Even though this will work, ' ...
                    'it is strongly advised to initialize all channels ' ...
                    'using the add_channels method!'])
                end
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
        function answerstruct = generic_request(obj, path, varargin)
            import matlab.net.http.*
            import matlab.net.http.field.*
            if nargin == 2
                request = matlab.net.http.RequestMessage('GET');
                response = request.send(path);
                answerstruct = response.Body.Data;
            elseif nargin == 3
                request = RequestMessage('POST', ...
                    [ContentTypeField('application/json'), ...
                    AcceptField('application/json')], varargin{1});
                response = request.send(path);
                answerstruct = response.Body.Data;
            else
                error('Incorrect number of arguments!')
            end       
            obj.generic_bluefors_error_handler(answerstruct)
        end

        % turns channel on or off
        % channel_nr: number of channel
        % status: either 'on' or 'off'
        function toggle_channel(obj, channel_nr, status)
            obj.initialized_checker('c', channel_nr)
            if strcmpi(status, 'on')
                tog = true;
            elseif strcmpi(status, 'off')
                tog = false;
            else
                error('Wrong status! Use on or off.')
            end
            path = obj.make_endpoint(obj.httpiport, 'channel', 'update');
            payload.channel_nr = channel_nr;
            payload.active = tog;
            obj.generic_request(path, payload)
            fprintf('Turned channel %i %s.\n', channel_nr, setstatus);
        end

        function temp = get_latest_channel_temp(obj, channel_nr)
            meas = obj.get_channel_temps_in_time(channel_nr, obj.cycle_time * 1.5);
            temp = meas.temperature(end);
        end
        
        % gets all temperature values of a specific channel measurement in
        % the last XX seconds
        % channel_number: number of channel
        % time_seconds: length of time interval in seconds
        % returns: struct with temperatures and timestamps
        function temps = get_channel_temps_in_time(obj, channel_number, time_seconds)
            obj.initialized_checker('c', channel_number)
            path = obj.make_endpoint(obj.httpiport, 'channel', ...
                    'historical-data');
            payload.start_time = obj.make_past_timestr(time_seconds);
            payload.stop_time = obj.make_timestr(now);
            payload.channel_nr = channel_number;
            payload.fields = {'temperature', 'timestamp'};
            meas = obj.generic_request(path, payload);
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
            obj.initialized_checker('h', heater_index)
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
            obj.generic_request(path, payload);
            fprintf('Turned heater %i %s.\n', heater_index, setstatus);
        end
           
        % sets specific power to heater
        % heater_index: number of heater
        % power: power in uW (microwatts, 1e-6 W)
        function set_heater_power(obj, heater_index, setpower)
            obj.initialized_checker('h', heater_index)
            path = obj.make_endpoint(obj.httpiport, 'heater', 'update');
            power_in_watts = setpower * 1e-6;
            payload.heater_nr = heater_index;
            payload.power = power_in_watts;
            obj.generic_request(path, payload);
            fprintf('Set heater %i to %i uW.\n', heater_index, setpower)
        end
        
        % reads current heater power
        % heater_index: number of heater
        % returns: power in uW (microwatts, 1e-6 W)
        function power = get_heater_power(obj, heater_index)
            obj.initialized_checker('h', heater_index)
            path = obj.make_endpoint(obj.httpiport, 'heater');
            payload.heater_nr = heater_index;
            answer = obj.generic_request(path, payload);
            power = answer.power * 1e6;
        end
        
        % reads current pid mode of heater
        % heater_index: heater number
        % returns: 0 for manual, 1 for pid
        function mode = get_pid_mode(obj, heater_index)
            obj.initialized_checker('h', heater_index)
            path = obj.make_endpoint(obj.httpiport, 'heater');
            payload.heater_nr = heater_index;
            mode = obj.generic_request(path, payload).pid_mode;
        end

        % toggles manual and pid mode 
        % heater_index: number of heater
        % setstatus: either 'manual' or 'pid' (case insensitive)
        function toggle_pid_mode(obj, heater_index, setstatus)
            obj.initialized_checker('h', heater_index)
            if strcmpi(setstatus, 'manual')
                if obj.get_pid_mode(heater_index) == 0
                    fprintf('Heater %i already in manual mode.\n', ...
                        heater_index)
                    return;
                end
                tog = 0;
            elseif strcmpi(setstatus, 'pid')
                if obj.get_pid_mode(heater_index) == 1
                    fprintf('Heater %i already in pid mode.\n', ...
                        heater_index)
                    return;
                end
                tog = 1;
            else
                error('Wrong status! Use on or off.')
            end

            path = obj.make_endpoint(obj.httpiport, 'heater', 'update');
            payload.heater_nr = heater_index;
            payload.pid_mode = tog;
            obj.generic_request(path, payload);
            fprintf('Turned heater %i to %s mode.\n', heater_index, setstatus);            
        end

        % changes the pid parameters of a heater
        % heater_index: heater number
        % prop: pid parameter proportional
        % int: pid parameter integral
        % dev: pid parameter derivative
        function set_pid_parameters(obj, heater_index, prop, int, dev)
            obj.initialized_checker('h', heater_index)            
            path = obj.make_endpoint(obj.httpiport, 'heater', 'update');
            payload.heater_nr = heater_index;
            payload.control_algorithm_settings.proportional = prop;
            payload.control_algorithm_settings.integral = int;
            payload.control_algorithm_setting.derivative = dev;
            obj.generic_request(path, payload);
            fprintf(['Set pid paramaters of heater %i to proportional: %s,'...
                'intergral: %s, derivative: %s.\n'], heater_index, prop, int, dev);
        end

        % sets a target_temperature (setpoint) for the pid control
        % heater_index: heater number
        % target_temp: target temperature in mK (milikelvin, 1e-3)
        function set_setpoint(obj, heater_index, setpoint)
            obj.initialized_checker('h', heater_index)            
            path = obj.make_endpoint(obj.httpiport, 'heater', 'update');
            payload.heater_nr = heater_index;
            payload.setpoint = setpoint * 1e-3;
            obj.generic_request(path, payload);
            fprintf('Set target temperature of pid for heater %i to %s mK.\n', ...
                heater_index, setpoint);
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


