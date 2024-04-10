classdef Logger
    properties
        logLevel
        logFile
    end

    methods
        function obj = Logger(logFile)
            obj.logLevel = 'INFO';
            obj.logFile = logFile;
        end

        function setLogLevel(obj, level)
            obj.logLevel = upper(level);
        end

        function logMessage(obj, level, message)
            if strcmp(upper(level), 'DEBUG') && strcmp(obj.logLevel, 'DEBUG')
                obj.writeToFile(['DEBUG: ', message]);
            elseif strcmp(upper(level), 'INFO') && (strcmp(obj.logLevel, 'DEBUG') || strcmp(obj.logLevel, 'INFO'))
                obj.writeToFile(['INFO: ', message]);
            elseif strcmp(upper(level), 'WARN') && (strcmp(obj.logLevel, 'DEBUG') || strcmp(obj.logLevel, 'INFO') || strcmp(obj.logLevel, 'WARN'))
                obj.writeToFile(['WARNING: ', message]);
            elseif strcmp(upper(level), 'ERROR') && (strcmp(obj.logLevel, 'DEBUG') || strcmp(obj.logLevel, 'INFO') || strcmp(obj.logLevel, 'WARN') || strcmp(obj.logLevel, 'ERROR'))
                obj.writeToFile(['ERROR: ', message]);
            end
        end

        function writeToFile(obj, message)
            fid = fopen(obj.logFile, 'a');
            if fid == -1
                error('Failed to open log file for writing');
            end
            fprintf(fid, '%s\n', message);
            fclose(fid);
        end

        function debug(obj, message)
            obj.logMessage('DEBUG', message);
        end

        function info(obj, message)
            obj.logMessage('INFO', message);
        end

        function warn(obj, message)
            obj.logMessage('WARN', message);
        end

        function error(obj, message)
            obj.logMessage('ERROR', message);
        end
    end
end
