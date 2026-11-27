\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{fulbright-slides}[2026/11/24 v0.1 Fulbright University Vietnam slide class]

% =====================================================================
%  FULBRIGHT UNIVERSITY VIETNAM SLIDE CLASS
%  File: <project>/style/fulbright-slides.cls
% ---------------------------------------------------------------------
%  Beamer class for talks that sit beside the working-paper kit
%  (fulbright.cls / workingpaper.cls). Academic in substance -- Latin
%  Modern serif throughout, the paper's theorem environments, apacite
%  citations, math-macros.tex -- with two consulting conventions:
%
%    * ACTION TITLES   frame titles are full-sentence takeaways (up to
%                      two lines), sitting on a thin crimson rule.
%                      \framesubtitle{...} becomes a small grey KICKER
%                      printed above the title ("Results . Calibration").
%    * TRACKER         the current section name in the top-right corner
%                      of every content slide.
%
%  Usage (in <project>/main.tex, with this file vendored under style/):
%
%     \documentclass{style/fulbright-slides}
%     \input{style/math-macros}
%     \title[Short title]{Full title}
%     \author[Short name]{Full name}
%     \institute{Fulbright University Vietnam}
%     \date{\today}
%     \classification{Macroeconomics}        % optional override
%     \begin{document}
%       \begin{frame}[plain,noframenumbering]\titlepage\end{frame}
%       \section{Motivation}                  % divider slide appears
%       \begin{frame}{An action title that states the takeaway}
%         \framesubtitle{Motivation}          % kicker
%         ...
%       \end{frame}
%       \backupslides                         % appendix; not counted
%     \end{document}
%
%  Paths follow the paper kit: \documentclass{style/...} resolves
%  relative to main.tex, so a bare `pdflatex main.tex` works.
% =====================================================================


% ---------------------------------------------------------------------
%  Options
%    nodividers     no automatic divider frame at each \section
%    <other>        passed to beamer (handout, aspectratio=43, 10pt...)
%  Defaults: aspectratio=169, 9pt, t (frame bodies top-aligned under
%  the title; pass `c` to centre). The layout is dense by default (9pt
%  body, 0.8cm margins, tight display skips) to leave room for maths;
%  pass `10pt` or `11pt` for a roomier body -- titles keep their size. `notheorems` is always passed so the
%  paper's theorem set (below) is defined here instead of beamer's.
% ---------------------------------------------------------------------
\newif\iffb@dividers  \fb@dividerstrue
\newif\iffb@backup    \fb@backupfalse

\DeclareOption{nodividers}{\fb@dividersfalse}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{beamer}}
\PassOptionsToClass{aspectratio=169,9pt,t,notheorems}{beamer}
\ProcessOptions\relax


% ---------------------------------------------------------------------
%  apacite vs. hyperref patch (same as workingpaper.cls; see the long
%  comment there). Beamer loads hyperref INSIDE the class, so the fake
%  \NAT@parse must exist before \LoadClass{beamer}.
% ---------------------------------------------------------------------
\@ifundefined{NAT@parse}{%
  \def\NAT@parse{This is a fake natbib command to fool hyperref.}%
}{}

\LoadClass{beamer}


% ---------------------------------------------------------------------
%  Packages
% ---------------------------------------------------------------------
\RequirePackage[T1]{fontenc}
\RequirePackage{lmodern}
\RequirePackage{anyfontsize}
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{bm}
\RequirePackage{booktabs}
\RequirePackage{tabularx}
\RequirePackage{appendixnumberbeamer}   % backup slides don't inflate N
\RequirePackage{apacite}

\usefonttheme{serif}
\bibliographystyle{apacite}

% apacite opens the bibliography with \section*{\refname}, which breaks
% inside a frame (and would fire a divider). The frame title carries
% "References" instead, so the heading is dropped.
\def\st@rtbibsection{}
\renewcommand{\bibliographytypesize}{\footnotesize}

\graphicspath{%
  {./}%
  {./graphs/}%
  {./figures/}%
  {./style/}%
}

\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator*{\plim}{plim}


% ---------------------------------------------------------------------
%  Brand tokens
% ---------------------------------------------------------------------
\definecolor{fulbrightcrimson}{HTML}{9E1B32}   % same as fulbright.cls
\definecolor{fbink}  {HTML}{1A1A1A}            % body text
\definecolor{fbgrey} {HTML}{6B6B6B}            % kicker, tracker, footer
\definecolor{fbrule} {HTML}{C8C8C8}            % footer hairline
\definecolor{fblight}{HTML}{F3EDEE}            % block tint

\newcommand{\fb@empty}{}
\newcommand{\fb@classification}{Macroeconomics}
\newcommand{\fb@titlelogo}{Stacked-Formal-Lock-Up.png}
\newcommand{\classification}[1]{\renewcommand{\fb@classification}{#1}}
\newcommand{\fb@footerlogo}{}
\newcommand{\titlelogo}[1]{\renewcommand{\fb@titlelogo}{#1}}
\newcommand{\footerlogo}[1]{\renewcommand{\fb@footerlogo}{#1}}  % {} = none
% The two lines below are read by newtex to vendor the logo files.
\titlelogo{Stacked-Formal-Lock-Up.png}
\footerlogo{Fulbright-Seal.png}

\newlength{\fb@margin}
\setlength{\fb@margin}{0.8cm}
\setbeamersize{text margin left=\fb@margin, text margin right=\fb@margin}


% ---------------------------------------------------------------------
%  Density: tighter display maths and lists. \normalsize resets the
%  display skips, so the override is appended to it.
% ---------------------------------------------------------------------
\g@addto@macro\normalsize{%
  \setlength{\abovedisplayskip}{5pt plus 2pt minus 2pt}%
  \setlength{\belowdisplayskip}{5pt plus 2pt minus 2pt}%
  \setlength{\abovedisplayshortskip}{2pt plus 2pt}%
  \setlength{\belowdisplayshortskip}{3pt plus 2pt minus 1pt}%
}
\setlength{\jot}{2pt}                       % row gap in align etc.
\setbeamertemplate{itemize/enumerate body begin}{\setlength{\itemsep}{1pt}}
\setbeamertemplate{itemize/enumerate subbody begin}{\setlength{\itemsep}{0pt}}


% ---------------------------------------------------------------------
%  Colours
% ---------------------------------------------------------------------
\setbeamercolor{normal text}      {fg=fbink, bg=white}
\setbeamercolor{structure}        {fg=fulbrightcrimson}
\setbeamercolor{alerted text}     {fg=fulbrightcrimson}
\setbeamercolor{frametitle}       {fg=fbink}
\setbeamercolor{framesubtitle}    {fg=fbgrey}
\setbeamercolor{tracker}          {fg=fbgrey}
\setbeamercolor{footline}         {fg=fbgrey}
\setbeamercolor{title}            {fg=fbink}
\setbeamercolor{subtitle}         {fg=fbgrey}
\setbeamercolor{titlebar}         {fg=fulbrightcrimson}
\setbeamercolor{section title}    {fg=fulbrightcrimson}
\setbeamercolor{section number}   {fg=fbgrey}
\setbeamercolor{section in toc}   {fg=fbink}
\setbeamercolor{block title}        {fg=fulbrightcrimson}
\setbeamercolor{block body}         {fg=fbink}
\setbeamercolor{block title example}{fg=fbink}
\setbeamercolor{block body example} {fg=fbink}
\setbeamercolor{block title alerted}{fg=fulbrightcrimson}
\setbeamercolor{block body alerted} {fg=fbink}
\setbeamercolor{bibliography entry author}{fg=fbink}
\setbeamercolor{bibliography entry note}  {fg=fbgrey}


% ---------------------------------------------------------------------
%  Fonts
% ---------------------------------------------------------------------
\setbeamerfont{frametitle}     {size=\fontsize{13}{15.5}, series=\bfseries}
% kicker = \framesubtitle; own font (framesubtitle inherits frametitle's
% bold, and bold small caps do not exist in Latin Modern)
\setbeamerfont{kicker}         {size=\fontsize{7}{8}, series=\mdseries, shape=\scshape}
\setbeamerfont{tracker}        {size=\fontsize{7}{8}, series=\mdseries, shape=\scshape}
\setbeamerfont{footline}       {size=\fontsize{6}{7}}
\setbeamerfont{title}          {size=\fontsize{17}{21}, series=\bfseries}
\setbeamerfont{subtitle}       {size=\large}
\setbeamerfont{author}         {size=\normalsize}
\setbeamerfont{institute}      {size=\small}
\setbeamerfont{date}           {size=\small}
\setbeamerfont{section title}  {size=\fontsize{17}{21}, series=\bfseries}
\setbeamerfont{section number} {size=\fontsize{40}{44}}
\setbeamerfont{block title}    {size=\normalsize, series=\bfseries}
\setbeamerfont{classification} {size=\scriptsize, shape=\scshape}


% ---------------------------------------------------------------------
%  Inner elements
% ---------------------------------------------------------------------
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{itemize items}[square]
\setbeamertemplate{enumerate items}[default]
\setbeamertemplate{theorems}[numbered]
\setbeamertemplate{bibliography item}{}
\setbeamertemplate{section in toc}{%
  \inserttocsectionnumber.\enspace\inserttocsection\par}
\setbeamertemplate{section in toc shaded}[default][35]
\setbeamertemplate{subsection in toc}{}
\setbeamertemplate{frametitle continuation}{}   % no "References I, II"


% ---------------------------------------------------------------------
%  Headline: just top padding. The tracker (current section) sits on
%  the kicker's row, right-aligned, inside the frame title below.
% ---------------------------------------------------------------------
\setbeamertemplate{headline}{\vskip4pt}


% ---------------------------------------------------------------------
%  Frame title: kicker (framesubtitle, left) and tracker (section,
%  right) on one small row, then the action title (one or two lines)
%  on a thin crimson rule. The box takes the title's natural height,
%  so a one-line title leaves no empty band above it.
% ---------------------------------------------------------------------
\setbeamertemplate{frametitle}{%
  \begin{beamercolorbox}[wd=\paperwidth, leftskip=\fb@margin,
                         rightskip=\fb@margin]{frametitle}%
    \usebeamerfont{frametitle}%
    \parbox{\dimexpr\paperwidth-2\fb@margin\relax}{%
      \raggedright
      \noindent\hbox to\linewidth{%
        {\mdseries\usebeamerfont{kicker}\usebeamercolor[fg]{framesubtitle}%
         \insertframesubtitle\strut}%
        \hfill
        {\mdseries\usebeamerfont{tracker}\usebeamercolor[fg]{tracker}%
         \insertsectionhead}}%
      \vskip-1pt
      \insertframetitle\strut}\par
    \nointerlineskip\vskip3pt%
    \leavevmode\textcolor{fulbrightcrimson}{%
      \rule{\dimexpr\paperwidth-2\fb@margin\relax}{0.6pt}}\par
  \end{beamercolorbox}%
  \vskip-6pt%
}


% ---------------------------------------------------------------------
%  Footline: hairline, short author . short title, n / N, seal
% ---------------------------------------------------------------------
\setbeamertemplate{footline}{%
  \hbox to\paperwidth{\hskip\fb@margin
    \textcolor{fbrule}{\rule{\dimexpr\paperwidth-2\fb@margin\relax}{0.4pt}}%
    \hss}%
  \vskip2.5pt%
  \hbox to\paperwidth{\hskip\fb@margin
    {\usebeamerfont{footline}\usebeamercolor[fg]{footline}%
     \insertshortauthor\enspace\textperiodcentered\enspace\insertshorttitle
     \hfill
     \insertframenumber\,/\,\inserttotalframenumber
     \ifx\fb@footerlogo\fb@empty\else
       \hskip6pt\raisebox{-0.3\height}{%
         \includegraphics[height=9pt]{\fb@footerlogo}}%
     \fi}%
    \hskip\fb@margin}%
  \vskip4pt%
}


% ---------------------------------------------------------------------
%  Title page: logo + classification line, crimson bar beside the title
% ---------------------------------------------------------------------
\setbeamertemplate{title page}{%
  \vbox to\dimexpr\paperheight-1.4cm\relax{%
  \begin{minipage}[t]{0.5\textwidth}%
    \ifx\fb@titlelogo\fb@empty\else
      \includegraphics[height=1.3cm]{\fb@titlelogo}%
    \fi
  \end{minipage}%
  \hfill
  \begin{minipage}[t]{0.45\textwidth}%
    \raggedleft
    {\usebeamerfont{classification}\color{fbgrey}\fb@classification\par}%
  \end{minipage}%
  \vskip0pt plus 1.6fill
  \hbox{%
    \textcolor{fulbrightcrimson}{\vrule width 2.5pt}%
    \hskip14pt
    \parbox[c]{0.85\textwidth}{%
      \vskip4pt
      {\usebeamerfont{title}\usebeamercolor[fg]{title}%
       \raggedright\inserttitle\par}%
      \ifx\insertsubtitle\@empty\else
        \vskip6pt
        {\usebeamerfont{subtitle}\usebeamercolor[fg]{subtitle}%
         \raggedright\insertsubtitle\par}%
      \fi
      \vskip4pt}}%
  \vskip18pt
  \hskip16.5pt\parbox[t]{0.85\textwidth}{%
    {\usebeamerfont{author}\insertauthor\par}%
    \ifx\insertinstitute\@empty\else
      \vskip2pt
      {\usebeamerfont{institute}\color{fbgrey}\insertinstitute\par}%
    \fi
    \vskip6pt
    {\usebeamerfont{date}\color{fbgrey}\insertdate\par}}%
  \vskip0pt plus 1fill}%
}


% ---------------------------------------------------------------------
%  Section dividers
%
%  Left: section number (or "Backup") and title on a crimson rule.
%  Right: agenda, current section in full ink, others shaded.
%  Plain + noframenumbering, so dividers don't count toward n / N.
% ---------------------------------------------------------------------
\setbeamertemplate{section page}{%
  \vfill
  \begin{minipage}[c]{0.46\textwidth}%
    {\usebeamerfont{section number}\usebeamercolor[fg]{section number}%
     \iffb@backup{\usebeamerfont{tracker}Backup}\else
       \insertsectionnumber\fi\par}%
    \vskip8pt
    \leavevmode\textcolor{fulbrightcrimson}{\rule{0.9\linewidth}{0.6pt}}\par
    \vskip8pt
    {\usebeamerfont{section title}\usebeamercolor[fg]{section title}%
     \raggedright\insertsectionhead\par}%
  \end{minipage}%
  \hfill
  \begin{minipage}[c]{0.46\textwidth}%
    \iffb@backup\else
      \small\tableofcontents[currentsection, hideallsubsections]%
    \fi
  \end{minipage}%
  \vfill
}

\AtBeginSection{%
  \iffb@dividers
    \begin{frame}[plain, noframenumbering]
      \usebeamertemplate{section page}
    \end{frame}
  \fi
}

% \backupslides: start the appendix with a "Backup" divider. Backup
% frames keep their own numbers but are excluded from the total.
\newcommand{\backupslides}{%
  \appendix
  \fb@backuptrue
  \section{Backup}%
}


% ---------------------------------------------------------------------
%  Blocks: no fill, a coloured bar down the left edge, bold heading.
%  The body is set in a box narrower than \linewidth, then placed beside
%  a rule that takes the box's full height. Theorems, definitions and
%  proofs all use these (theorem/proof: crimson; example: grey).
% ---------------------------------------------------------------------
\newsavebox{\fb@blockbox}
\newlength{\fb@barwidth}  \setlength{\fb@barwidth}{2pt}
\newlength{\fb@bargap}    \setlength{\fb@bargap}{7pt}

\newcommand{\fb@blockbegin}[1]{% #1 = 0 block, 1 alerted, 2 example
  \par\vskip4pt plus 2pt
  \begin{lrbox}{\fb@blockbox}%
  \begin{minipage}{\dimexpr\linewidth-\fb@barwidth-\fb@bargap\relax}%
    \abovedisplayskip3pt plus 1pt\belowdisplayskip3pt plus 1pt
    \ifx\insertblocktitle\@empty\else
      {\usebeamerfont*{block title}\usebeamercolor[fg]{\fb@titlecol{#1}}%
       \insertblocktitle\par}\vskip1pt
    \fi
    \usebeamerfont{block body}\usebeamercolor[fg]{block body}}
\newcommand{\fb@titlecol}[1]{%
  \ifcase#1 block title\or block title alerted\or block title example\fi}
\newcommand{\fb@blockend}[1]{%
  \end{minipage}%
  \end{lrbox}%
  \noindent\hbox{\textcolor{#1}{\vrule width\fb@barwidth}%
    \hskip\fb@bargap
    \vbox{\vskip2pt\copy\fb@blockbox\vskip2pt}}%
  \par\vskip4pt plus 2pt}

\setbeamertemplate{block begin}{\fb@blockbegin{0}}
\setbeamertemplate{block end}{\fb@blockend{fulbrightcrimson}}
\setbeamertemplate{block alerted begin}{\fb@blockbegin{1}}
\setbeamertemplate{block alerted end}{\fb@blockend{fulbrightcrimson}}
\setbeamertemplate{block example begin}{\fb@blockbegin{2}}
\setbeamertemplate{block example end}{\fb@blockend{fbrule}}


% ---------------------------------------------------------------------
%  Theorem environments (same names as workingpaper.cls), rendered as
%  beamer blocks and numbered sequentially through the talk.
% ---------------------------------------------------------------------
\theoremstyle{plain}
\newtheorem{theorem}{Theorem}
\newtheorem{proposition}{Proposition}
\newtheorem{lemma}{Lemma}
\newtheorem{corollary}{Corollary}

\theoremstyle{definition}
\newtheorem{definition}{Definition}
\newtheorem{model}{Model}
\newtheorem{example}{Example}
\newtheorem{problem}{Problem}

\theoremstyle{remark}
\newtheorem{remark}{Remark}
\newtheorem{assumption}{Assumption}

\newenvironment{solution}
  {\begin{proof}[Solution]}
  {\end{proof}}


\endinput
