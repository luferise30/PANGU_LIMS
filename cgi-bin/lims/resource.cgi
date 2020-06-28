#!/usr/bin/perl -w
use strict;
use CGI qw(:standard);
use CGI::Carp qw ( fatalsToBrowser );
use DBI;
use lib "lib/";
use lib "lib/pangu";
use pangu;
use userCookie;

my $userCookie = new userCookie;
my $userId = (cookie('cid')) ? $userCookie->checkCookie(cookie('cid')) : 0;
if(!$userId)
{
	print header;
	print <<eof;
	<h2>Error</h2>
	Please <a onclick="openDialog('login.cgi');">login</a> first!
	<script type="text/javascript">
		openDialog('login.cgi');
		loadingHide();
	</script>
eof
    exit;
}


my $commoncfg = readParam();
my $htdocs = $commoncfg->getProperty('HTDOCS');
my $dbuser = $commoncfg->getProperty('USERNAME');
my $dbpass = $commoncfg->getProperty('PASSWORD');
my $dbhost = $commoncfg->getProperty('DBHOST');
my $dbdata = $commoncfg->getProperty('DATABASE');

#my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);
my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);
undef $/;# enable slurp mode
my $html = data();

my $active = 0;
my $activeDetector = 0;
my $cookieProject = cookie('project') || '';

my $projects = '';
my $project=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'project'");# ORDER BY name
$project->execute();
if($project->rows > 0)
{
	my $projectResult;
	while (my @project = $project->fetchrow_array())
	{
		@{$projectResult->{$project[2]}} = @project;
	}
	foreach (sort {uc ($a) cmp uc($b)} keys %$projectResult)
	{
		my @project = @{$projectResult->{$_}};
		$project[2] = "Project: Name N/A, please edit!" unless($project[2]);
		$projects .= "<li><a href='project.cgi?projectId=$project[0]'>$project[2]</a></li>\n";
		$active = $activeDetector if ($cookieProject eq $project[0]);
		$activeDetector++;
	}
}

$html =~ s/\$projects/$projects/;
$html =~ s/\$active/$active/;
#$html =~ s/\$commoncfg->\{HTDOCS}/$htdocs/g;
$html =~ s/\$commoncfg->\{HTDOCS}/$htdocs/g;

print header(-cookie=>cookie(-name=>'menu',-value=>1));
print $html;

sub data{
my $data=<<'HTML';
<div id="projects">
	<ul>
		$projects
		<li><a href='projectNew.cgi'>New project</a></li>
	</ul>
</div>
<script>
loadingHide();
$( "#projects" ).tabs({
	// loading spinner
	beforeLoad: function(event, ui) {
		ui.panel.html('<img src="$htdocs/css/images/loading.gif" style="vertical-align:middle;"> Loading...');
	},
	create: function (e, ui) {
		loadingShow();
	},
	activate: function (e, ui) {
		loadingShow();
	},
	active: $active
}).addClass( "ui-tabs-vertical ui-helper-clearfix" );
$( "#projects li" ).removeClass( "ui-corner-top" ).addClass( "ui-corner-left" );
$( "#projects .ui-tabs-panel" ).css('padding','0px 2px');
</script>
HTML
return $data;}
