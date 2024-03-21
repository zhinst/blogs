% Kramers–Kronig Test Applied to Impedance Measurements of Electrical Circuits 
%
% Copyright (C) 2017 Zurich Instruments 
% 
% This software may be modified and distributed under the terms 
% of the MIT license. See the LICENSE file for details.
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
clear; close all; clc;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
file_name = 'Impedance_Measurement_MFIA.csv';
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Reading measured data from file
% file_name = 'Impedance.txt';
fid = fopen(file_name,'r');
data = dlmread(file_name,'',3,0);
fclose(fid);
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Extracting frequency and impedance
freq = data(:,1)';
realZ = data(:,2)';
imagZ = data(:,3)';
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
freqExt = freq;
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
figure('Name','Impedance Spectroscopy','NumberTitle','on');

set(gca,'FontSize',12,...
    'LineWidth',2,...
    'Color',[1 1 1],...
    'Box','on');

h = semilogx(freqExt,realZ);
set(h,'LineWidth',4,'LineStyle','-','Color','b')
hold on;
h = semilogx(freq,imagZ);
set(h,'LineWidth',4,'LineStyle','--','Color','r')
grid on;

title('Impedance Spectroscopy','fontsize',12,'fontweight','n','color','k');
xlabel('Frequency  [Hz]','fontsize',12,'fontweight','n','color','k');
ylabel('Impedance  [\Omega]','fontsize',12,'fontweight','n','fontangle','n','color','k');

h = legend('Real Z','Imag Z');
set(h,'Box','on','Color','w','Location','NorthEast','FontSize',12,'FontWeight','n','FontAngle','n')

xlim([0.01 100e3])
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Removing the series resistor (It improves the precision in high frequencies)
realZ_RemovedSeries = realZ - realZ(end);

%%% Calculating the imaginary part using the KK relations. 
NumFreq = length(freqExt);
FreqKK = freq(1+2:NumFreq-2);
KKimagZ = zeros(1,length(FreqKK));
for nn = 3:NumFreq-2
    integrand = realZ_RemovedSeries./(freqExt.^2 - freqExt(nn)^2);
    KKimagZ(nn - 2) = (2*freqExt(nn)/pi)*(trapz(freqExt(1:nn-1),integrand(1:nn-1)) + trapz(freqExt(nn+1:NumFreq),integrand(nn+1:NumFreq)));
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
figure('Name','Impedance Spectroscopy','NumberTitle','on');

set(gca,'FontSize',12,...
    'LineWidth',2,...
    'Color',[1 1 1],...
    'Box','on');

h = semilogx(freq,imagZ);
set(h,'LineWidth',2.5,'LineStyle','--','Color','r')
hold on;
h = semilogx(FreqKK,KKimagZ);
set(h,'LineWidth',2.5,'LineStyle','-','Color','g')
grid on;

title('Impedance Spectroscopy','fontsize',12,'fontweight','n','color','k');
xlabel('Frequency  [Hz]','fontsize',12,'fontweight','n','color','k');
ylabel('Reactance  [\Omega]','fontsize',12,'fontweight','n','fontangle','n','color','k');

h = legend('Measurement','Kramers-Kronig');
set(h,'Box','on','Color','w','Location','NorthEast','FontSize',12,'FontWeight','n','FontAngle','n')

xlim([1 max(freq)])
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Calculating the real part using the KK relations.  
imagZ_RemovedSeries = imagZ;
NumFreq = length(freqExt);
FreqKK = freq(1+2:NumFreq-2);
KKrealZ = zeros(1,length(FreqKK));
for nn = 3:NumFreq-2
    integrand = imagZ_RemovedSeries.*freqExt./(freqExt.^2 - freqExt(nn)^2);
    KKrealZ(nn - 2) = -(2/pi)*(trapz(freqExt(1:nn-1),integrand(1:nn-1)) + trapz(freqExt(nn+1:NumFreq),integrand(nn+1:NumFreq)));
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
figure('Name','Impedance Spectroscopy','NumberTitle','on');

set(gca,'FontSize',12,...
    'LineWidth',2,...
    'Color',[1 1 1],...
    'Box','on');

h = semilogx(freq,realZ);
set(h,'LineWidth',2.5,'LineStyle','--','Color','r')
hold on;
h = semilogx(FreqKK,KKrealZ + realZ(end));
set(h,'LineWidth',2.5,'LineStyle','-','Color','g')
grid on;

title('Impedance Spectroscopy','fontsize',12,'fontweight','n','color','k');
xlabel('Frequency  [Hz]','fontsize',12,'fontweight','n','color','k');
ylabel('Resistance  [\Omega]','fontsize',12,'fontweight','n','fontangle','n','color','k');

h = legend('Measurement','Kramers-Kronig');
set(h,'Box','on','Color','w','Location','NorthEast','FontSize',12,'FontWeight','n','FontAngle','n')

xlim([0.01 max(freq)])
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
