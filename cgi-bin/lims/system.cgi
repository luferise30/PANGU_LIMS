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

my $button = "<div class='ui-state-highlight ui-corner-all' style='padding: 0 .7em;'>
	<h2>System tools</h2>
	<button onclick='refresh(\"general\")'>Refresh</button>
	<button class='ui-state-error-text' onclick='deleteItem(0)' title='Delete Orphan Records'>Delete Orphan Records</button>
	<button class='ui-state-error-text' onclick='deleteItem(0,\"delTempFiles\")' title='Delete Cached Files'>Delete Cached Files</button>
	</div>\n";

$html =~ s/\$button/$button/g;
$html =~ s/\$\$/$$/g;


print header(-cookie=>cookie(-name=>'general',-value=>7));
print $html;

sub data{
my $data=<<'HTML';
$button
<script>
buttonInit();
loadingHide();
</script>
HTML
return $data;}
