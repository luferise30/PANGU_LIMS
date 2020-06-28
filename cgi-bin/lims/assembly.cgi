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
my $cgibin = $commoncfg->getProperty('CGIBIN');

my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);

undef $/;# enable slurp mode
my $html = data();

my $targetId = param ('targetId') || '';
my $cookieAssembly = cookie('assembly') || '';
my $asbProjectContent = '';
my $active = 0;
my $activeDetector = 0;
my $assemblyList = '';
if($targetId)
{
	my $assembly=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'assembly' AND x = ?");
	$assembly->execute($targetId);
	while(my @assembly = $assembly->fetchrow_array())
	{
		$assemblyList .= "<h2><a href='$cgibin/assemblyList.cgi?assemblyId=$assembly[0]'>$assembly[2] Version $assembly[3] ($assembly[10])</a></h2><div><img src='$htdocs/css/images/loading.gif'>Loading...</div>";
		$active = $activeDetector if ($assembly[0] eq $cookieAssembly);
		$activeDetector++;
	}
	$assemblyList .= "<h2><a href='$cgibin/assemblyNew.cgi?targetId=$targetId'>Create a new assembly</a></h2><div><img src='$htdocs/css/images/loading.gif'>Loading...</div>";
	$asbProjectContent = $targetId;
}
else
{
	print header(-type=>'text/html',-status=>'402 Invalid operation');
	exit;
}
my $collapsible = ($activeDetector > 1) ? 'true' : 'false';

$html =~ s/\$assemblyList/$assemblyList/g;
$html =~ s/\$asbProjectContent/$asbProjectContent/g;
$html =~ s/\$\$/$$/g;
$html =~ s/\$active/$active/g;
$html =~ s/\$collapsible/$collapsible/g;
$html =~ s/\$cgibin/$cgibin/g;
$html =~ s/\$htdocs/$htdocs/g;

print header(-cookie=>cookie(-name=>'asbProjectContent',-value=>$asbProjectContent));
print $html;

sub data{
my $data=<<'HTML';

<div id="assembly$asbProjectContent">
	$assemblyList
</div>
<script>
buttonInit();
loadingHide();
$("#assembly$asbProjectContent").accordion({
	active:$active,
	collapsible: $collapsible,
	create:function(event, ui) {
		ui.panel.load(ui.header.find('a').attr('href'));
	},
	activate:function(event, ui) {
		ui.newPanel.load(ui.newHeader.find('a').attr('href'));
	},
	heightStyle: "content"
});
</script>
HTML
return $data;}
