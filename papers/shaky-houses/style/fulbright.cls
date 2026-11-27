\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{fulbright}[2026/04/22 v0.2 Fulbright University Vietnam working-paper class]

% =====================================================================
%  FULBRIGHT UNIVERSITY VIETNAM WORKING-PAPER CLASS
%  File: <project>/style/fulbright.cls
% ---------------------------------------------------------------------
%  University-affiliated brand (Fulbright University Vietnam,
%  Macroeconomics programme). Wraps the shared workingpaper base with
%  Fulbright-specific masthead copy, logo, and typography (12pt body).
%
%  Usage (in <project>/main.tex, with this file vendored under style/):
%
%     \documentclass{style/fulbright}
%     \title{...}  \author{...}  \date{\today}
%     \classification{Macroeconomics}     % optional override
%     \begin{document}\maketitle ... \bibliography{references}\end{document}
%
%  See ochna.cls for rationale on path-in-\documentclass.
% =====================================================================


% ---------------------------------------------------------------------
%  Options -- forwarded to the shared base. Note default is 12pt,
%  not 11pt: Fulbright's house style runs slightly larger than Ochna's.
% ---------------------------------------------------------------------
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{style/workingpaper}}
\ExecuteOptions{a4paper,11pt}
\ProcessOptions\relax

\LoadClass{style/workingpaper}


% ---------------------------------------------------------------------
%  Typography overrides for the 12pt body size
%
%  The base class registers \wp@sectionsize etc. as mutable macros;
%  titlesec re-expands them at each section heading, so a \renewcommand
%  here takes effect without re-calling \titleformat.
% ---------------------------------------------------------------------
\renewcommand{\wp@sectionsize}     {\fontsize{14pt}{17pt}}
\renewcommand{\wp@subsectionsize}  {\fontsize{13pt}{16pt}}
\renewcommand{\wp@subsubsectionsize}{\fontsize{12pt}{15pt}}

% Body: 11pt text with 13pt leading (overrides the base's 11/14).
% \AtBeginDocument hooks execute in registration order, so this runs
% after the base's hook and wins.
\AtBeginDocument{%
  \fontsize{11pt}{13pt}\selectfont
}


% ---------------------------------------------------------------------
%  Fulbright brand defaults
% ---------------------------------------------------------------------
\classification{Macroeconomics}
\subject{}                                     % e.g. \subject{Graduate Assignment}
\logofile{Stacked-Formal-Lock-Up.png}          % resolved via \graphicspath
\logoscale{0.25}
\mastheadbottomskip{-15pt}


% ---------------------------------------------------------------------
%  Fulbright brand colour -- crimson from the Fulbright University
%  Vietnam identity guide (approximate; adjust if official value differs).
% ---------------------------------------------------------------------
\definecolor{fulbrightcrimson}{HTML}{9E1B32}


\endinput
