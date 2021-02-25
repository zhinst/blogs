%% Getting started with APIs – MATLAB
% 
% This code reproduces the example shown in Zurich Instruments' video
% introduction to its textual APIs.
%
% The example is simple: it creates a connection to an instrument pre-configured
% through the LabOne graphical user interface, it reads a single sample from
% a demodulator and it closes the connection.
%
% Please note that no error handling is considered in this simple example;
% for more information on this important topic, please refer to the Zurich
% Instruments Programming Manual.
% 
% Copyright (C) 2021 Zurich Instruments
% This software may be modified and distributed under the terms
% of the MIT license. See the LICENSE file for details.
%

%% Connect to the Instrument
device_id = 'DEVXXXX';  % Please change the device ID matching your instrument's
apilevel = 6;           % Please update the API level to 1 if you are using HF2LI 
[device, ~] = ziCreateAPISession(device_id, apilevel);

%% Read out a single sample from a demodulator
sample = ziDAQ('getSample', ['/' device '/demods/0/sample']);
disp(sample)

%% Convert X and Y into polar representation 
R = abs(sample.x + 1j*sample.y);
theta = atan2d(sample.y,sample.x);

fprintf('R:\t\t %0.1e V\n', R);
fprintf('theta:\t %0.1f deg\n', theta);

%%
% Get samples in a slow loop
run_time = 20;   % run the loop for 20 seconds

t0 = tic;
while toc(t0) < run_time
    pause(0.1);       % sleep for 100 ms
    sample = ziDAQ('getSample', ['/' device '/demods/0/sample']);
    disp(sample)
end
toc(t0)

%% Get help 
help ziDAQ
doc ziDAQ


%% Get the list of nodes
flags = int64(2);      % flags can be 0, 1, 2, 3
ziDAQ('listNodes',device, flags)

