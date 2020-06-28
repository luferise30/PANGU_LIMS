#!/usr/bin/perl -w
use strict;
use CGI qw(:standard);
use CGI::Carp qw ( fatalsToBrowser );
use DBI;
use lib "lib/";
use lib "lib/pangu";
use pangu;
use user;
use userCookie;

my $userCookie = new userCookie;
my $userId = (cookie('cid')) ? $userCookie->checkCookie(cookie('cid')) : 0;
exit if (!$userId);

my $user = new user;
my $userDetail = $user->getAllFieldsWithUserId($userId);
my $userName = $userDetail->{"userName"};

my $commoncfg = readParam();
my $htdocs = $commoncfg->getProperty('HTDOCS');
my $dbuser = $commoncfg->getProperty('USERNAME');
my $dbpass = $commoncfg->getProperty('PASSWORD');
my $dbhost = $commoncfg->getProperty('DBHOST');
my $dbdata = $commoncfg->getProperty('DATABASE');
my $tmpdir = $commoncfg->getProperty('TMPDIR');
my $tempurl = $commoncfg->getProperty('TMPURL');

my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);

my $alignmentId = param ('alignmentId') || '';

unless (-e $tmpdir)
{
	mkdir $tmpdir;
}
my %seqType = (
	0=>'Assembled',
	1=>'BAC-Insert',
	2=>'BAC-Circularized',
	3=>'BAC-NonVector',
	4=>'BAC-Gapped',
	5=>'Partial',
	6=>'Vector/Mixer',
	7=>'Mixer',
	8=>'SHORT',
	97=>'Piece',
	98=>'BES',
	99=>'Genome'
	);
my %bacAssignType = (
	0=>'',
	1=>'TagValid',
	2=>'BesValid',
	3=>'TagValid+BesValid',
	4=>'TagForced'
	);
my %seqDir = (
	0 => "NA",
	1 => "f",
	2 => "r"
	);

print header;

if($alignmentId)
{
	unlink ("$tmpdir/$alignmentId.aln.html") if(-e "$tmpdir/$alignmentId.aln.html");
	if(!-e "$tmpdir/$alignmentId.aln.html")
	{
		my $getAlignment = $dbh->prepare("SELECT * FROM alignment WHERE id = ?");
		$getAlignment->execute($alignmentId);
		my @getAlignment = $getAlignment->fetchrow_array();
		my $queryDirection = ($getAlignment[8] < $getAlignment[9]) ? "+" : "-";
		my $subjectDirection = ($getAlignment[10] < $getAlignment[11]) ? "+" : "-";
		my $getSequenceA = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
		$getSequenceA->execute($getAlignment[2]);
		my @getSequenceA =  $getSequenceA->fetchrow_array();
		$getSequenceA[5] = commify($getSequenceA[5]);
		my $getSequenceB = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
		$getSequenceB->execute($getAlignment[3]);
		my @getSequenceB = $getSequenceB->fetchrow_array();
		$getSequenceB[5] = commify($getSequenceB[5]);
		$getAlignment[5] = commify($getAlignment[5]);
		$getAlignment[8] = commify($getAlignment[8]);
		$getAlignment[9] = commify($getAlignment[9]);
		$getAlignment[10] = commify($getAlignment[10]);
		$getAlignment[11] = commify($getAlignment[11]);
		$getAlignment[8] = "<a class='ui-state-error-text' title='Seq End'>$getAlignment[8]</a>" if($getAlignment[8] eq 1 || $getAlignment[8] eq $getSequenceA[5]);
		$getAlignment[9] = "<a class='ui-state-error-text' title='Seq End'>$getAlignment[9]</a>" if($getAlignment[9] eq 1 || $getAlignment[9] eq $getSequenceA[5]);
		$getAlignment[10] = "<a class='ui-state-error-text' title='Seq End'>$getAlignment[10]</a>" if($getAlignment[10] eq 1 || $getAlignment[10] eq $getSequenceB[5]);
		$getAlignment[11] = "<a class='ui-state-error-text' title='Seq End'>$getAlignment[11]</a>" if($getAlignment[11] eq 1 || $getAlignment[11] eq $getSequenceB[5]);

		open (ALN,">$tmpdir/$alignmentId.aln.html") or die "can't open file: $tmpdir/$alignmentId.aln.html";
		print ALN <<END;
	<table id='alignment$alignmentId$$' class='display'>
	<thead><tr><th></th><th>Seqs</th><th>Length</th><th>Identity</th><th>Alignment Length</th><th>Start</th><th></th><th>End</th></tr></thead>
	<tbody>
		<tr>
			<td><b>Query</b></td>
			<td>$getSequenceA[2] <sup onclick='closeDialog();openDialog("seqView.cgi?seqId=$getSequenceA[0]")' title='View this sequence'>$seqType{$getSequenceA[3]}</sup> $bacAssignType{$getSequenceA[7]}</td>
			<td>$getSequenceA[5]</td>
			<td rowspan='2'><a title='E-value:$getAlignment[12] \nBit-score:$getAlignment[13]'>$getAlignment[4]%</a></td>
			<td rowspan='2'>$getAlignment[5]</td>
			<td>$getAlignment[8]</td>
			<td>$queryDirection</td>
			<td>$getAlignment[9]</td>
		</tr>
		<tr>
			<td><b>Subject</b></td>
			<td>$getSequenceB[2] <sup onclick='closeDialog();openDialog("seqView.cgi?seqId=$getSequenceB[0]")' title='View this sequence'>$seqType{$getSequenceB[3]}</sup> $bacAssignType{$getSequenceB[7]}</td>
			<td>$getSequenceB[5]</td>
			<td>$getAlignment[10]</td>
			<td>$subjectDirection</td>
			<td>$getAlignment[11]</td>
		</tr>
	</tbody>
	</table>
<script>
\$('#dialog').dialog("option", "title", "Selected Alignment Between $getSequenceA[2]($getSequenceA[0]) & $getSequenceB[2]($getSequenceB[0])");
\$( "#dialog" ).dialog( "option", "buttons", [ { text: "OK", click: function() {closeDialog(); } } ] );
</script>
END
		close (ALN);
	}
	print <<END;
	<script>
	parent.loadingHide();
	parent.closeDialog();
	parent.openDialog('$tempurl/$alignmentId.aln.html');
	</script>
END

}
else
{
	print <<END;
<script>
	parent.loadingHide();
	parent.errorPop('Please give an alignment Id!');
</script>
END
}
