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

print header;
print $html;

sub data{
my $data=<<'HTML';
<form id="newVector" name="newVector" action="vectorSave.cgi" enctype="multipart/form-data" method="post" target="hiddenFrame">
	<table>
	<tr><td style='text-align:right'><label for="newVectorName"><b>Vector Name</b></label></td><td><input class='ui-widget-content ui-corner-all' name="name" id="newVectorName" size="40" type="text" maxlength="32" /></td></tr>
	<tr><td style='text-align:right'><label for="newVectorDescription"><b>Description</b></label><br>(Sequence)</td><td><textarea class='ui-widget-content ui-corner-all' name="description" id="newVectorDescription" cols="50" rows="10"></textarea></td></tr>
	</table>
</form>
<script>
$('#dialog').dialog("option", "title", "New Vector");
$( "#dialog" ).dialog( "option", "buttons", [{ text: "Save", click: function() { submitForm('newVector'); } }, { text: "Cancel", click: function() {closeDialog(); } } ] );
</script>
HTML
return $data;}
