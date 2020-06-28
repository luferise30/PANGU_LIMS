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

my $active = 0;
my $activeDetector = 0;
my $cookieBox = cookie('box') || '';

my $freezerId = param ('freezerId') || '';
my $button;
my $boxes = '';
if ($freezerId)
{
	my $boxInFreezer=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'box' AND o = $freezerId ORDER BY name");
	$boxInFreezer->execute();
	while (my @boxInFreezer = $boxInFreezer->fetchrow_array())
	{
		$boxes = "<div id='boxesInFreezer$freezerId$$'><ul>\n" unless($boxes);
		$boxes .= "<li><a href='box.cgi?boxId=$boxInFreezer[0]'>Box: $boxInFreezer[2]</a></li>\n";
		$active = $activeDetector if ($cookieBox eq $boxInFreezer[0]);
		$activeDetector++;
	}
	my $engaged = $boxInFreezer->rows;
	my $freezer=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$freezer->execute($freezerId);
	my @freezer = $freezer->fetchrow_array();
	$freezer[8] = escapeHTML($freezer[8]);
	$freezer[8] =~ s/\n/<br>/g;
	my $maxLoads= $freezer[4]*$freezer[5]*$freezer[6];
	my $disengaged = $maxLoads - $engaged;
	$button = "<div class='ui-state-highlight ui-corner-all' style='padding: 0 .7em;'>";
	$button .= "<div style='float: right; margin-top: .3em; margin-right: .3em;' id='progressbar$freezerId$$'><div class='progress-label'>$engaged/$maxLoads loads</div></div>";	
	$button .= "<button style='z-index: 1;float: right; margin-top: .3em; margin-right: .3em;' onclick='openDialog(\"boxNew.cgi?freezerId=$freezerId\")'>New box</button>" if ($disengaged > 0);
	$button .= "<div style='position: relative;'><h3><a id='freezer$freezerId$$' onmouseover='editIconShow(\"freezer$freezerId$$\")' onmouseout='editIconHide(\"freezer$freezerId$$\")' onclick='openDialog(\"freezerEdit.cgi?freezerId=$freezerId\")' title='Edit/Delete'>Freezer $freezer[2]</a></h3></div>";
	$button .= "$freezer[8]" if ($freezer[8]);	
	$html =~ s/\$maxLoads/$maxLoads/g;
	$html =~ s/\$engaged/$engaged/g;
	unless($boxes)
	{
		$button .= "<p class='ui-state-error ui-corner-all' style='padding: .7em;'><span class='ui-icon ui-icon-alert' style='float: left; margin-right: .3em;'></span>
			<strong>No box in this freezer.</strong></p>";
	}
	$button .= "</div>";
	$boxes .= "</ul></div>\n" if($boxes);
	print header(-cookie=>cookie(-name=>'freezer',-value=>$freezerId));
}
else
{
	print header(-type=>'text/html',-status=>'402 Invalid operation');
	exit;
}
$html =~ s/\$freezerId/$freezerId/g;
$html =~ s/\$\$/$$/g;
$html =~ s/\$button/$button/g;
$html =~ s/\$boxes/$boxes/g;
$html =~ s/\$active/$active/g;
$html =~ s/\$htdocs/$htdocs/g;

print $html;

sub data{
my $data=<<'HTML';
$button
$boxes
<script>
buttonInit();
$( "#progressbar$freezerId$$" ).progressbar({
	max:$maxLoads,
	value: $engaged
});
loadingHide();
$( "#boxesInFreezer$freezerId$$" ).tabs({
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
});
</script>
HTML
return $data;}
