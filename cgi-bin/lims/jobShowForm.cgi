#!/usr/bin/perl -w
use strict;
use CGI qw(:standard);
use CGI::Carp qw ( fatalsToBrowser ); 
use JSON::XS;
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
print header;
my @jobId;
my $jobId;
my $hiddenJobList=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'job' ORDER BY name");
$hiddenJobList->execute();
while (my @hiddenJobList = $hiddenJobList->fetchrow_array())
{
	my $jobDetails = decode_json $hiddenJobList[8];
	if ($hiddenJobList[2] =~ /^-(.*)/)
	{
		push @jobId, $1;
		$jobId->{$1} = $1 ."-".$jobDetails->{'name'};
	}
}
@jobId = sort @jobId;
my $jobList = 'No Hidden Jobs!';
$jobList = checkbox_group(-name=>'jobId',
	-values=>[@jobId],
	-labels=>\%{$jobId},
	-columns=>2) if (@jobId);

$html =~ s/\$jobList/$jobList/g;

print $html;

sub data{
my $data=<<'HTML';
<form id="jobShow" name="jobShow" action="jobShow.cgi" enctype="multipart/form-data" method="post" target="hiddenFrame">
<h3>Please check hidden jobs to show:</h3>
$jobList
</form>
<script>
$('#dialog').dialog("option", "title", "Manage Hidden Jobs");
$( "#dialog" ).dialog( "option", "buttons", [{ text: "Show", click: function() { submitForm('jobShow'); } }, { text: "Cancel", click: function() {closeDialog(); } } ] );
</script>
HTML
return $data;}
