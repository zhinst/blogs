% Time-Domain Response of Lock-in Filters
%
% Copyright (C) 2017 Zurich Instruments 
% 
% This software may be modified and distributed under the terms 
% of the MIT license. See the LICENSE file for details.
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function DemodFilterResponse(order)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% DemodFilterResponse takes the filter order as a positive integer and
% plots the step and impulse response of the demodulator filter with the
% corresponding order. 

%%% time constant
TC = 981.1e-6;
%%% number of time constant
Num = 20;
%%% time variable
t = linspace(0, Num*TC, 1e4);
%%% normalized time variable
tau = t/TC; 

%%% Zero part
LimitNegative = -1;
EmptyTime = linspace(LimitNegative,0,1e3);
EbptyRes = zeros(1,1e3);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
%%% Iterative calculation of the step response 
term = 1;
LastTerm = 1;
if order>1
    for n = 2:order
        LastTerm = LastTerm.*tau/(n-1);
        term = term + LastTerm;
    end
end
StepResponse = 1 - exp(-tau).*term;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
figure('Name','Step Response','NumberTitle','on');

set(gca,'FontSize',12,...
    'LineWidth',2,...
    'Color',[1 1 1],...
    'Box','on');

title('Step Response','fontsize',12,'fontweight','n','color','k');
xlabel('Time  [ t / t_c ]','fontsize',12,'fontweight','n','color','k');
ylabel('Response','fontsize',12,'fontweight','n','fontangle','n','color','k');

grid on
hold on

h = plot([EmptyTime tau], [EbptyRes StepResponse]);
set(h,'LineWidth',3,'LineStyle','-','Color','b')

h = legend(['Order ' num2str(order)]);
set(h,'Box','on','Color','w','Location','SouthEast','FontSize',15,'FontWeight','b','FontAngle','n')

xlim([LimitNegative,Num])
ylim([-0.05 1.05])

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
%%% Impulse response
ImpulseResponse = ((tau.^(order-1))./(factorial(order-1)*TC)).*exp(-tau);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
figure('Name','Impulse Response','NumberTitle','on');

set(gca,'FontSize',12,...
    'LineWidth',2,...
    'Color',[1 1 1],...
    'Box','on');

title('Impulse Response','fontsize',12,'fontweight','n','color','k');
xlabel('Time  [ t / t_c ]','fontsize',12,'fontweight','n','color','k');
ylabel('Response  [s^{-1}]','fontsize',12,'fontweight','n','fontangle','n','color','k');

grid on
hold on

h = plot([EmptyTime tau], [EbptyRes ImpulseResponse]);
set(h,'LineWidth',3,'LineStyle','-','Color','r')

h = legend(['Order ' num2str(order)]);
set(h,'Box','on','Color','w','Location','NorthEast','FontSize',15,'FontWeight','b','FontAngle','n')

xlim([LimitNegative,Num])
ylim(max(ImpulseResponse)*[-0.05 1.05])
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
end
