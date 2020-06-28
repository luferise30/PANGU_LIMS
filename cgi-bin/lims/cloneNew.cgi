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

my $libraryId = param ('libraryId') || '';

my $library=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
$library->execute($libraryId);
my @library = $library->fetchrow_array();

$html =~ s/\$libraryId/$libraryId/g;
$html =~ s/\$libraryName/$library[2]/g;
$html =~ s/\$nofPlates/$library[3]/g;

print header;
print $html;

sub data{
my $data=<<'HTML';
<form id="newClone" name="newClone" action="cloneSave.cgi" enctype="multipart/form-data" method="post" target="hiddenFrame">
	<input name="libraryId" id="libraryId" type="hidden" value="$libraryId" />
	This operation will generate a new clone list for $nofPlates plate(s) in $libraryName and may take several minutes.<br>
	<input type="checkbox" id="reformatSourceCloneName" name="reformat" value="1" checked="checked"><label for="reformatSourceCloneName">Reformat Source Clone Names (for rearraying library only).</label>
</form>
<script>
$('#dialog').dialog("option", "title", "Generate Clone List");
$( "#dialog" ).dialog( "option", "buttons", [{ text: "Generate", click: function() { submitForm('newClone'); } }, { text: "Cancel", click: function() {closeDialog(); } } ] );
</script>
HTML
return $data;}
