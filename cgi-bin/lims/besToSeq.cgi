#!/usr/bin/perl -w
use strict;
use CGI qw(:standard);
use CGI::Carp qw ( fatalsToBrowser );
use JSON::XS; #JSON::XS is recommended to be installed for handling JSON string of big size
use DBI;
use lib "lib/";
use lib "lib/pangu";
use pangu;
use user;
use userConfig;
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

my $userConfig = new userConfig;

my $alignEngineList;
$alignEngineList->{'blastn'} = "blast+/bin/blastn";
$alignEngineList->{'BLAT'} = "blat";
my $windowmasker = 'blast+/bin/windowmasker';
my $makeblastdb = 'blast+/bin/makeblastdb';

my $libraryId = param ('libraryId') || '';
my $targetId = param ('targetId') || '';

my $identityBesToSeq = param ('identityBesToSeq') || $userConfig->getFieldValueWithUserIdAndFieldName($userId,"BESTOSEQIDENTITY");
my $minOverlapBesToSeq = param ('minOverlapBesToSeq') || $userConfig->getFieldValueWithUserIdAndFieldName($userId,"BESTOSEQMINOVERLAP");

print header;

if($libraryId && $targetId)
{
	my $pid = fork();
	if ($pid) {
		print <<END;
<script>
	parent.closeDialog();
	parent.informationPop("It's running! This processing might take a while.");
</script>
END
	}
	elsif($pid == 0){
		close (STDOUT);
		#connect to the mysql server
		my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);

		my $target=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
		$target->execute($targetId);
		my @target = $target->fetchrow_array();

		open (SEQALL,">$tmpdir/$targetId.$$.seq") or die "can't open file: $tmpdir/$targetId.$$.seq";
		if($target[1] eq 'library')
		{
			my $getClones = $dbh->prepare("SELECT * FROM clones WHERE sequenced > 0 AND libraryId = ?");
			$getClones->execute($targetId);
			while(my @getClones = $getClones->fetchrow_array())
			{
				my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o < 50 AND name LIKE ?");
				$getSequences->execute($getClones[1]);
				while(my @getSequences = $getSequences->fetchrow_array())
				{
					my $sequenceDetails = decode_json $getSequences[8];
					$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
					$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
					$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
					$sequenceDetails->{'sequence'} =~ tr/a-zA-Z/N/c; #replace nonword characters.;
					$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
					print SEQALL ">$getSequences[0]\n$sequenceDetails->{'sequence'}\n";
				}
			}
		}
		if($target[1] eq 'genome')
		{
			my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o = 99 AND x = ?");
			$getSequences->execute($targetId);
			while(my @getSequences = $getSequences->fetchrow_array())
			{
				my $sequenceDetails = decode_json $getSequences[8];
				$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
				$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
				$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
				$sequenceDetails->{'sequence'} =~ tr/a-zA-Z/N/c; #replace nonword characters.;
				$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
				print SEQALL ">$getSequences[0]\n$sequenceDetails->{'sequence'}\n";
			}
		}
		close(SEQALL);

		open (BES,">$tmpdir/$libraryId.$$.bes") or die "can't open file: $tmpdir/$libraryId.$$.bes";
		my $getBesSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o = 98 AND x = ?");
		$getBesSequences->execute($libraryId);
		while(my @getBesSequences = $getBesSequences->fetchrow_array())
		{
			my $sequenceDetails = decode_json $getBesSequences[8];
			$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
			$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
			$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
			$sequenceDetails->{'sequence'} =~ tr/a-zA-Z/N/c; #replace nonword characters.;
			$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
			print BES ">$getBesSequences[0]\n$sequenceDetails->{'sequence'}\n";
		}
		close(BES);

		open (BLAST,">$tmpdir/$libraryId.$$.blastn") or die "can't open file: $tmpdir/$libraryId.$$.blastn";
		system( "$makeblastdb -in $tmpdir/$targetId.$$.seq -dbtype nucl" );
		open (CMD,"$alignEngineList->{'blastn'} -query $tmpdir/$libraryId.$$.bes -db $tmpdir/$targetId.$$.seq -dust no -evalue 1e-200 -perc_identity $identityBesToSeq -num_threads 8 -outfmt 6 |") or die "can't open CMD: $!";
		while(<CMD>)
		{
			/^#/ and next;
			my @hit = split("\t",$_);
			next if($hit[3] < $minOverlapBesToSeq);
			my $getAlignment = $dbh->prepare("SELECT * FROM alignment WHERE query = ? AND subject = ?");
			$getAlignment->execute($hit[0],$hit[1]);
			if($getAlignment->rows > 0)
			{
				next;
			}
			else
			{
				print BLAST $_;
			}
		}
		close(CMD);
		close(BLAST);
		open (BLAST,"$tmpdir/$libraryId.$$.blastn") or die "can't open file: $tmpdir/$libraryId.$$.blastn";
		while(<BLAST>)
		{
			my @hit = split("\t",$_);
			#write to alignment
			my $insertAlignment=$dbh->prepare("INSERT INTO alignment VALUES ('', 'BEStoSEQ\_1e-200\_$identityBesToSeq\_$minOverlapBesToSeq', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)");
			$insertAlignment->execute(@hit);
		}
		close(BLAST);

		unlink("$tmpdir/$libraryId.$$.bes");
		unlink("$tmpdir/$targetId.$$.seq");
		unlink("$tmpdir/$targetId.$$.seq.nhr");
		unlink("$tmpdir/$targetId.$$.seq.nin");
		unlink("$tmpdir/$targetId.$$.seq.nsq");
		unlink("$tmpdir/$libraryId.$$.blastn");
	}
	else{
		die "couldn't fork: $!\n";
	}
}
else
{
	print <<END;
<script>
	parent.errorPop("Please give an assembly id!");
</script>
END
}
