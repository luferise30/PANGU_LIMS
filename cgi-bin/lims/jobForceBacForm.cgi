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
exit if (!$userId);

my $commoncfg = readParam();
my $htdocs = $commoncfg->getProperty('HTDOCS');
my $dbuser = $commoncfg->getProperty('USERNAME');
my $dbpass = $commoncfg->getProperty('PASSWORD');
my $dbhost = $commoncfg->getProperty('DBHOST');
my $dbdata = $commoncfg->getProperty('DATABASE');

my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);

undef $/;# enable slurp mode
my $html = data();

my @jobId = param('jobId');
print header;
unless(@jobId)
{
	my $jobList=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'job' ORDER BY name");
	$jobList->execute();
	while (my @jobList = $jobList->fetchrow_array())
	{
		next if ($jobList[2] =~ /^-/);
		push @jobId, $jobList[2];
	}
}
my $jobList = 'No Jobs Available or Selected.';
my $jobId;
for(@jobId)
{
	$jobId->{$_} = $_;
}
$jobList = checkbox_group(-name=>'jobId',
	-values=>[@jobId],
	-default=>[@jobId],
	-onclick=>'return false;',
	-labels=>\%{$jobId},
	-columns=>8) if (@jobId);

$html =~ s/\$jobList/$jobList/g;

print $html;

sub data{
my $data=<<'HTML';
<form id="runForceBac" name="runForceBac" action="jobForceBac.cgi" enctype="multipart/form-data" method="post" target="hiddenFrame">
<h3>Are you going to assign BAC Id for the below jobs (Forcing Mode)?</h3>
	<table>
	<tr><td style='text-align:right;white-space: nowrap;'><label for="runForceBacJobList"><b>Selected Jobs<b></label></td><td>$jobList</td></tr>
	</table>
</form>
<script>
$('#dialog').dialog("option", "title", "Assign BAC Id (Forcing Mode)");
$( "#dialog" ).dialog( "option", "buttons", [{ text: "Run", click: function() { submitForm('runForceBac'); } }, { text: "Cancel", click: function() {closeDialog(); } } ] );
</script>
HTML
return $data;}
