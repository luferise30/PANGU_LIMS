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

my $assemblyId = param ('assemblyId') || '';
my $seqOne = param ('seqOne') || '';
my $seqTwo = param ('seqTwo') || '';
my $redo = param ('redo') || '0';
my $hidden = param ('hidden') || '1';
my $filter = param ('filter') || '0';

my $alignmentCheckFormUrl = "alignmentCheckForm.cgi";
if($assemblyId)
{
	$alignmentCheckFormUrl .= "?assemblyId=$assemblyId";
}
my $blastTwoseqFormUrl = "blastTwoseqForm.cgi";
if($assemblyId)
{
	$blastTwoseqFormUrl .= "?assemblyId=$assemblyId";
}

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

if($seqOne || $seqTwo)
{
	if($seqOne && $seqTwo)
	{
		unlink ("$tmpdir/$seqOne-$seqTwo.aln.html") if $redo;
		if(!-e "$tmpdir/$seqOne-$seqTwo.aln.html")
		{
			my $getSequenceA = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$getSequenceA->execute($seqOne);
			my @getSequenceA =  $getSequenceA->fetchrow_array();
			$getSequenceA[5] = commify($getSequenceA[5]);
			my $getSequenceB = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$getSequenceB->execute($seqTwo);
			my @getSequenceB = $getSequenceB->fetchrow_array();
			$getSequenceB[5] = commify($getSequenceB[5]);
			open (ALN,">$tmpdir/$seqOne-$seqTwo.aln.html") or die "can't open file: $tmpdir/$seqOne-$seqTwo.aln.html";
			print ALN <<END;
	<table id='alignment$$' class='display'><thead><tr><th>$getSequenceA[2]</th><th>Query Length</th><th>$getSequenceB[2]</th><th>Subject Length</th><th>Identity %</th><th>Alignment Length</th><th>Query Start</th><th>Query End</th><th></th><th>Subject Start</th><th>Subject End</th></tr></thead><tbody>
END
			my $getAlignment = $dbh->prepare("SELECT * FROM alignment WHERE query = ? AND subject = ? AND hidden < ?");
			$getAlignment->execute($getSequenceA[0],$getSequenceB[0],$hidden);
			while(my @getAlignment = $getAlignment->fetchrow_array())
			{
				my $direction = ($getAlignment[10] < $getAlignment[11]) ? "+":"-";
				$getAlignment[5] = commify($getAlignment[5]);
				$getAlignment[8] = commify($getAlignment[8]);
				$getAlignment[9] = commify($getAlignment[9]);
				$getAlignment[10] = commify($getAlignment[10]);
				$getAlignment[11] = commify($getAlignment[11]);
				$getAlignment[8] = "<a class='ui-state-error-text' title='Seq End'>$getAlignment[8]</a>" if($getAlignment[8] eq 1 || $getAlignment[8] eq $getSequenceA[5]);
				$getAlignment[9] = "<a class='ui-state-error-text' title='Seq End'>$getAlignment[9]</a>" if($getAlignment[9] eq 1 || $getAlignment[9] eq $getSequenceA[5]);
				$getAlignment[10] = "<a class='ui-state-error-text' title='Seq End'>$getAlignment[10]</a>" if($getAlignment[10] eq 1 || $getAlignment[10] eq $getSequenceB[5]);
				$getAlignment[11] = "<a class='ui-state-error-text' title='Seq End'>$getAlignment[11]</a>" if($getAlignment[11] eq 1 || $getAlignment[11] eq $getSequenceB[5]);
				print ALN "<tr>
					<td><a onclick='closeDialog();openDialog(\"seqView.cgi?seqId=$getSequenceA[0]\")' title='View this sequence'>$seqType{$getSequenceA[3]}</a> ($getSequenceA[4]) $bacAssignType{$getSequenceA[7]}</td>
					<td>$getSequenceA[5]</td>
					<td><a onclick='closeDialog();openDialog(\"seqView.cgi?seqId=$getSequenceB[0]\")' title='View this sequence'>$seqType{$getSequenceB[3]}</a> ($getSequenceB[4]) $bacAssignType{$getSequenceB[7]}</td>
					<td>$getSequenceB[5]</td>
					<td><a title='E-value:$getAlignment[12] \nBit-score:$getAlignment[13]'>$getAlignment[4]</a></td>
					<td>$getAlignment[5]</td>
					<td>$getAlignment[8]</td>
					<td>$getAlignment[9]</td>
					<td>$direction</td>
					<td>$getAlignment[10]</td>
					<td>$getAlignment[11]</td>
					</tr>";
			}
			$alignmentCheckFormUrl .= "&seqOne=$seqOne&seqTwo=$seqTwo";
			$blastTwoseqFormUrl .= "&seqOne=$seqOne&seqTwo=$seqTwo";
			print ALN <<END;
</tbody></table>
<script>
\$('#dialog').dialog("option", "title", "Alignment Between $getSequenceA[2]($seqOne) & $getSequenceB[2]($seqTwo)");
\$( "#dialog" ).dialog( "option", "buttons", [ { text: "New Check", click: function() {  closeDialog();openDialog('$alignmentCheckFormUrl'); } }, { text: "reRun BLAST", click: function() { closeDialog();openDialog('$blastTwoseqFormUrl'); } }, { text: "OK", click: function() {closeDialog(); } } ] );
\$('#dialog').dialog("option", "width", 1000);
\$( "#alignment$$" ).dataTable({
	"scrollY": "400px",
	"scrollCollapse": true,
	"paging": false,
	"searching": false
});
</script>
END
			close (ALN);
		}
		print <<END;
		<script>
		parent.loadingHide();
		parent.closeDialog();
		parent.openDialog('$tempurl/$seqOne-$seqTwo.aln.html');
		</script>
END
	}
	else
	{
		my $querySeq = ($seqOne) ? $seqOne : $seqTwo;
		unlink ("$tmpdir/$querySeq.aln.html") if $redo;
		if(!-e "$tmpdir/$querySeq.aln.html")
		{
			my $getSequenceA = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$getSequenceA->execute($querySeq);
			my @getSequenceA =  $getSequenceA->fetchrow_array();
			$getSequenceA[5] = commify($getSequenceA[5]);
			open (ALN,">$tmpdir/$querySeq.aln.html") or die "can't open file: $tmpdir/$querySeq.aln.html";
			print ALN <<END;
<table id='alignment$$' class='display'><thead><tr><th>Query</th><th>Query Length</th><th>Subject</th><th>Subject Length</th><th>Identity %</th><th>Alignment Length</th><th>Query Start</th><th>Query End</th><th></th><th>Subject Start</th><th>Subject End</th></tr></thead><tbody>
END
			my $getSequenceBline;
			my $getAlignment = $dbh->prepare("SELECT * FROM alignment WHERE query = ? AND hidden < ?");
			$getAlignment->execute($getSequenceA[0],$hidden);
			while(my @getAlignment = $getAlignment->fetchrow_array())
			{
				my $direction = ($getAlignment[10] < $getAlignment[11]) ? "+":"-";
				$getAlignment[5] = commify($getAlignment[5]);
				unless (exists $getSequenceBline->{$getAlignment[3]})
				{
					my $getSequenceB = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
					$getSequenceB->execute($getAlignment[3]);
					@{$getSequenceBline->{$getAlignment[3]}} = $getSequenceB->fetchrow_array();
					$getSequenceBline->{$getAlignment[3]}[5] = commify($getSequenceBline->{$getAlignment[3]}[5]);
				}
				next if ($filter && ($getSequenceA[2] eq $getSequenceBline->{$getAlignment[3]}[2]));
				$getAlignment[8] = commify($getAlignment[8]);
				$getAlignment[9] = commify($getAlignment[9]);
				$getAlignment[10] = commify($getAlignment[10]);
				$getAlignment[11] = commify($getAlignment[11]);
				$getAlignment[8] = "<a class='ui-state-error-text' title='Seq End'>$getAlignment[8]</a>" if($getAlignment[8] eq 1 || $getAlignment[8] eq $getSequenceA[5]);
				$getAlignment[9] = "<a class='ui-state-error-text' title='Seq End'>$getAlignment[9]</a>" if($getAlignment[9] eq 1 || $getAlignment[9] eq $getSequenceA[5]);
				$getAlignment[10] = "<a class='ui-state-error-text' title='Seq End'>$getAlignment[10]</a>" if($getAlignment[10] eq 1 || $getAlignment[10] eq $getSequenceBline->{$getAlignment[3]}[5]);
				$getAlignment[11] = "<a class='ui-state-error-text' title='Seq End'>$getAlignment[11]</a>" if($getAlignment[11] eq 1 || $getAlignment[11] eq $getSequenceBline->{$getAlignment[3]}[5]);
				print ALN "<tr>
					<td><a onclick='closeDialog();openDialog(\"seqView.cgi?seqId=$getSequenceA[0]\")' title='View this sequence'>$seqType{$getSequenceA[3]}</a> ($getSequenceA[4]) $bacAssignType{$getSequenceA[7]}</td>
					<td>$getSequenceA[5]</td>
					<td><a onclick='closeDialog();openDialog(\"seqView.cgi?seqId=$getSequenceBline->{$getAlignment[3]}[0]\")' title='View this sequence'>$getSequenceBline->{$getAlignment[3]}[2]</a> $seqType{$getSequenceBline->{$getAlignment[3]}[3]} ($getSequenceBline->{$getAlignment[3]}[4]) $bacAssignType{$getSequenceBline->{$getAlignment[3]}[7]}</td>
					<td>$getSequenceBline->{$getAlignment[3]}[5]</td>
					<td><a title='E-value:$getAlignment[12] \nBit-score:$getAlignment[13]'>$getAlignment[4]</a></td>
					<td>$getAlignment[5]</td>
					<td>$getAlignment[8]</td>
					<td>$getAlignment[9]</td>
					<td>$direction</td>
					<td>$getAlignment[10]</td>
					<td>$getAlignment[11]</td>
					</tr>";
			}
			$alignmentCheckFormUrl .= "&seqOne=$querySeq";
			$blastTwoseqFormUrl .= "&seqOne=$querySeq";
			print ALN <<END;
</tbody></table>
<script>
\$('#dialog').dialog("option", "title", "Alignment of $getSequenceA[2] ($querySeq)");
\$( "#dialog" ).dialog( "option", "buttons", [ { text: "New Check", click: function() {  closeDialog();openDialog('$alignmentCheckFormUrl'); } }, { text: "reRun BLAST", click: function() { closeDialog();openDialog('$blastTwoseqFormUrl'); } }, { text: "OK", click: function() {closeDialog(); } } ] );
\$('#dialog').dialog("option", "width", 1000);
\$( "#alignment$$" ).dataTable({
	"scrollY": "400px",
	"scrollCollapse": true,
	"paging": false
});
</script>
END
			close (ALN);
		}

		print <<END;
		<script>
		parent.loadingHide();
		parent.closeDialog();
		parent.openDialog('$tempurl/$querySeq.aln.html');
		</script>
END
	}
}
else
{
	print <<END;
<script>
	parent.loadingHide();
	parent.errorPop('Please give at least one seq name!');
</script>
END
}
