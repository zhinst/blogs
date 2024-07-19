%% -----------------------------------------------------------------------
% Copyright 2024 Zurich Instruments AG
% 
% This example demonstrates how to perform Q-Control on a resonator using 
% a lock-in amplifer like MFLI or UHFLI. The instrument needs PID and MF
% or MD options.
%
% Clear and close everything
close all; clear; clc;
% ------------------------------------------------------------------------

%% Required parameters ---------------------------------------------------
% Parameters: device serial numbers, interface type, data server address
% and port, api level

%%% UHFLI
% device = 'dev2730';         % Device serial number in the rear panel
% interface = '1GbE';         % When data server is not on device
% host = '127.0.0.1';         % Address of data server away from device

%%% MFLI
device = 'dev4022';         % Device serial number in the rear panel
interface = 'PCIe';         % When data server runs on device
host = '10.42.5.62';        % Address of data server on device

port = 8004;                % Port data server listen to
apilevel = 6;               % Maximum API level for MFLI
% ------------------------------------------------------------------------

%% Connection to device --------------------------------------------------
% Close current API sessions
clear ziDAQ

% Create an API session to the data server
ziDAQ('connect', host, port, apilevel);

% Establish a connection between data server and device
ziDAQ('connectDevice', device, interface);
% ------------------------------------------------------------------------

%% Settings --------------------------------------------------------------
% Initial settings for Q control
ziDAQ('syncSetInt',  ['/' device '/system/preset/index'], 0);
ziDAQ('syncSetInt',  ['/' device '/system/preset/load'], 1);
pause(3);
% Define all the  settings in a "cell"
device_settings = {
    % Signal Output
    ['/' device '/sigouts/0/on'],               0;
    ['/' device '/sigouts/0/imp50'],            0;
    ['/' device '/sigouts/0/add'],              0;
    ['/' device '/sigouts/0/range'],            1.0;
    ['/' device '/sigouts/0/offset'],           0;
    ['/' device '/sigouts/0/diff'],             0;
    ['/' device '/sigouts/0/amplitudes/0'],     0;
    ['/' device '/sigouts/0/amplitudes/1'],     0;
    ['/' device '/sigouts/0/amplitudes/2'],     0;
    ['/' device '/sigouts/0/amplitudes/3'],     0;
    ['/' device '/sigouts/0/enables/0'],        0;
    ['/' device '/sigouts/0/enables/1'],        1;
    ['/' device '/sigouts/0/enables/2'],        1;
    ['/' device '/sigouts/0/enables/3'],        1;
    % Signal Input
    ['/' device '/sigins/0/imp50'],             1;
    ['/' device '/sigins/0/float'],             0;
    ['/' device '/sigins/0/diff'],              0;
    ['/' device '/sigins/0/ac'],                0;
    ['/' device '/sigins/0/range'],             0.3;
    % Demodulator
    ['/' device '/extrefs/*/enable'],           0;
    ['/' device '/demods/*/oscselect'],         0;
    ['/' device '/demods/*/harmonic'],          1;
    ['/' device '/demods/0/phaseshift'],        0.0;
    ['/' device '/demods/1/phaseshift'],        0.0;
    ['/' device '/demods/2/phaseshift'],        0.0;
    ['/' device '/demods/3/phaseshift'],        90.0;
    ['/' device '/demods/0/adcselect'],         0;
    % PIDs
    ['/' device '/pids/*/enable'],              0;
    ['/' device '/pids/2/input'],               0;
    ['/' device '/pids/3/input'],               1;
    ['/' device '/pids/2/inputchannel'],        0;
    ['/' device '/pids/3/inputchannel'],        0;
    ['/' device '/pids/2/setpoint'],            0;
    ['/' device '/pids/3/setpoint'],            0;
    ['/' device '/pids/2/demod/timeconstant'],  0.5e-3;
    ['/' device '/pids/3/demod/timeconstant'],  0.5e-3;
    ['/' device '/pids/2/demod/order'],         4;
    ['/' device '/pids/3/demod/order'],         4;
    ['/' device '/pids/2/demod/harmonic'],      1;
    ['/' device '/pids/3/demod/harmonic'],      1;
    ['/' device '/pids/2/output'],              0;
    ['/' device '/pids/3/output'],              0;
    ['/' device '/pids/2/outputchannel'],       2;
    ['/' device '/pids/3/outputchannel'],       3;
    ['/' device '/pids/2/center'],              0;
    ['/' device '/pids/3/center'],              0;
    ['/' device '/pids/2/limitlower'],          -0.5;
    ['/' device '/pids/3/limitlower'],          -0.5;
    ['/' device '/pids/2/limitupper'],          +0.5;
    ['/' device '/pids/3/limitupper'],          +0.5;
    ['/' device '/pids/2/p'],                   0;
    ['/' device '/pids/3/p'],                   0;
    ['/' device '/pids/2/i'],                   0;
    ['/' device '/pids/3/i'],                   0;
    ['/' device '/pids/2/d'],                   0;
    ['/' device '/pids/3/d'],                   0;
    ['/' device '/pids/2/keepint'],             0;
    ['/' device '/pids/3/keepint'],             0;
};
ziDAQ('set', device_settings);
% ------------------------------------------------------------------------

%% Drive Signal Output ---------------------------------------------------
% Drive the resonator around its resonance
resonance_frequency = 1.84342276e6; % [Hz]
driving_amplitude = 0.1;            % [V]
device_settings = {
    % Signal Output
    ['/' device '/oscs/0/freq'],            resonance_frequency;
    ['/' device '/sigouts/0/amplitudes/1'], driving_amplitude;
    ['/' device '/pids/2/enable'],          1;
    ['/' device '/pids/3/enable'],          1;
    ['/' device '/sigouts/0/on'],           1;
};
ziDAQ('set', device_settings);
% ------------------------------------------------------------------------

%% Apply feedback gain ---------------------------------------------------
% Depending on the level and sign of the feedback gain we can control the
% q-factor in different direction and intensity.
feedback_gain = -10;    % []
feadback_settings = {
    ['/' device '/pids/2/p'],   feedback_gain;
    ['/' device '/pids/3/p'],   feedback_gain;
};
ziDAQ('set', feadback_settings);
% ------------------------------------------------------------------------
