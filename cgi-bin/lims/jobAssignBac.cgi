#!/usr/bin/perl -w
use strict;
use CGI qw(:standard);
use CGI::Carp qw ( fatalsToBrowser );
use Bio::SeqIO;
use LWP::Simple qw/getstore/;
use JSON::XS; #JSON::XS is recommended to be installed for handling JSON string of big size
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

my $blastn = 'blast+/bin/blastn';
my $jobdir = $commoncfg->getProperty('JOBDIR');
my $tagMatchIdentity = 100; #identities for tags
my $besMatchIdentity = 98; #identities for bes
my $tagMatchPercent = 0.80; #total percent of matched tags
my $minCloneTagNumber = 5;
my $format = 'fasta';
my @jobId = param('jobId');
my $goodOnly = param ('goodOnly') || '';

print header;
my $pid = fork();
if ($pid) {
	print <<END;
<script>
	parent.closeDialog();
	parent.refresh("menu");
	parent.informationPop("It's running! This processing might take several minutes.");
</script>
END
}
elsif($pid == 0){
	close (STDOUT);
	my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);
	#connect to the mysql server
	foreach my $input (sort {$a <=> $b} @jobId)
	{
		my $outdir = "$jobdir/$input";
		unless (-e $outdir)
		{
			mkdir $outdir;
		}
		open (ALLLOG,">>$jobdir/jobs.log") or die "can't open file: $jobdir/jobs.log";
		print ALLLOG "Assign BAC ID for Job: $input\n";
		close(ALLLOG);
		open (LOG,">>$outdir/$input.log") or die "can't open file: $outdir/$input.log";
		#associate BAC and sequence
		my $updateJobToRunning=$dbh->do("UPDATE matrix SET barcode = '-1' WHERE container LIKE 'job' AND (name LIKE '$input' OR name LIKE '-$input')");
		my $assignedSequenceNumber = 0;
		my $jobToPool = $dbh->prepare("SELECT parent FROM link WHERE type LIKE 'poolJob' AND child = ?");
		$jobToPool->execute($input);
		while(my @jobToPool = $jobToPool->fetchrow_array())
		{
			#get clone list
			my $cloneTagNumber;
			my $cloneBesNumber;
			my $tagTotalNumber = 0;
			my $besTotalNumber = 0;
			open (TAG,">$tmpdir/$input.$$.tag") or die "can't open file: $tmpdir/$input.$$.tag";
			open (BES,">$tmpdir/$input.$$.bes") or die "can't open file: $tmpdir/$input.$$.bes";
			my $poolToClone = $dbh->prepare("SELECT child FROM link WHERE type LIKE 'poolClone' AND parent = ?");
			$poolToClone->execute($jobToPool[0]);
			while (my @poolToClone = $poolToClone->fetchrow_array())
			{
				#get tag list
				my $cloneToTag = $dbh->prepare("SELECT matrix.* FROM matrix,clones WHERE matrix.container LIKE 'tag' AND (matrix.name LIKE clones.name OR matrix.name LIKE clones.origin) AND clones.name LIKE ? ORDER BY matrix.o");
				$cloneToTag->execute($poolToClone[0]);
				while (my @cloneToTag = $cloneToTag->fetchrow_array())
				{
					$cloneTagNumber->{$cloneToTag[2]}++;
					$tagTotalNumber++;
					print TAG ">$cloneToTag[2].$cloneToTag[3]\n$cloneToTag[8]\n";
				}
				#get BES list
				my $cloneToBes = $dbh->prepare("SELECT matrix.* FROM matrix,clones WHERE matrix.container LIKE 'sequence' AND matrix.o = 98 AND (matrix.name LIKE clones.name OR matrix.name LIKE clones.origin) AND clones.name LIKE ? ORDER BY matrix.z");
				$cloneToBes->execute($poolToClone[0]);
				while (my @cloneToBes = $cloneToBes->fetchrow_array())
				{
					$cloneBesNumber->{$cloneToBes[2]}++;
					$besTotalNumber++;
					my $sequenceDetails = decode_json $cloneToBes[8];
					$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
					$sequenceDetails->{'sequence'} =~ tr/a-zA-Z/N/c; #replace nonword characters.
					next unless ($sequenceDetails->{'sequence'});
					print BES ">$cloneToBes[2].$cloneToBes[6]\n$sequenceDetails->{'sequence'}\n";
				}
			}
			close (BES);
			close (TAG);
			my $jobToSequence;
			if($goodOnly)
			{
				$jobToSequence = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND (o = 1 OR o = 2) AND x = ?"); #get circularized or inserted sequences only
			}
			else
			{
				$jobToSequence = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND (o = 1 OR o = 2 OR o = 3 OR o = 4) AND x = ?"); #get circularized or inserted sequences, non-vector or gapped sequences
			}
			$jobToSequence->execute($input);
			while(my @jobToSequence = $jobToSequence->fetchrow_array() )
			{
				my $bacIdAssigned = 0;
				my $sequenceDetails = decode_json $jobToSequence[8];
				$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
				$sequenceDetails->{'sequence'} =~ tr/a-zA-Z/N/c; #replace nonword characters.
				next unless ($sequenceDetails->{'sequence'});
				open (SEQ,">$tmpdir/$jobToSequence[0].seq") or die "can't open file: $tmpdir/$jobToSequence[0].seq";
				print SEQ ">$jobToSequence[0]\n$sequenceDetails->{'sequence'}";
				close (SEQ);
				if($tagTotalNumber > 0)
				{
					my $matchedTagNumber;
					open (CMD,"$blastn -query $tmpdir/$jobToSequence[0].seq -subject $tmpdir/$input.$$.tag -dust no -max_target_seqs 10000 -outfmt 6 |") or die "can't open CMD: $!";
					while(<CMD>)
					{
						my @blastLine = split /\t/, $_;
						next if ($blastLine[2] < $tagMatchIdentity);
						my ($bac,$tagId)  = split /\./,$blastLine[1];
						$matchedTagNumber->{$bac}++;
					}
					close(CMD);
					for (sort { $matchedTagNumber->{$b} <=> $matchedTagNumber->{$a} } keys(%$matchedTagNumber))
					{
						print LOG "$jobToSequence[0]\t$_\t$cloneTagNumber->{$_}\t$matchedTagNumber->{$_}\t";
						if (($matchedTagNumber->{$_}/$cloneTagNumber->{$_} > $tagMatchPercent) && ($cloneTagNumber->{$_} >= $minCloneTagNumber))
						{
							my $updateSequence=$dbh->prepare("UPDATE matrix SET name = ?, z = ?, barcode = 1 WHERE id = ?");
							$updateSequence->execute($_,$matchedTagNumber->{$_},$jobToSequence[0]);
							my $sequencedStatus = 0;
							my $getSequenced = $dbh->prepare("SELECT * FROM clones WHERE name LIKE ? OR origin LIKE ?");
							$getSequenced->execute($_,$_);
							while (my @getSequenced = $getSequenced->fetchrow_array())
							{
								$sequencedStatus = $getSequenced[6];
							}
							if ($jobToSequence[3] == 1 || $jobToSequence[3] == 2)
							{
								my $updateClone=$dbh->prepare("UPDATE clones SET sequenced = ? WHERE name LIKE ? OR origin LIKE ?");
								$updateClone->execute($jobToSequence[3],$_,$_);
								my $updateFpcClone=$dbh->prepare("UPDATE matrix SET x = ? WHERE container LIKE 'fpcClone' AND name LIKE ?");
								$updateFpcClone->execute($jobToSequence[3],$_);
							}
							elsif($jobToSequence[3] == 3)
							{
								if($sequencedStatus != 1 || $sequencedStatus != 2)
								{
									my $updateClone=$dbh->prepare("UPDATE clones SET sequenced = ? WHERE name LIKE ? OR origin LIKE ?");
									$updateClone->execute($jobToSequence[3],$_,$_);
									my $updateFpcClone=$dbh->prepare("UPDATE matrix SET x = ? WHERE container LIKE 'fpcClone' AND name LIKE ?");
									$updateFpcClone->execute($jobToSequence[3],$_);
								}
							}
							elsif($jobToSequence[3] == 4)
							{
								if($sequencedStatus != 1 || $sequencedStatus != 2 || $sequencedStatus != 3)
								{
									my $updateClone=$dbh->prepare("UPDATE clones SET sequenced = ? WHERE name LIKE ? OR origin LIKE ?");
									$updateClone->execute($jobToSequence[3],$_,$_);
									my $updateFpcClone=$dbh->prepare("UPDATE matrix SET x = ? WHERE container LIKE 'fpcClone' AND name LIKE ?");
									$updateFpcClone->execute($jobToSequence[3],$_);
								}
							}
							else
							{
								if($sequencedStatus != 1 || $sequencedStatus != 2 || $sequencedStatus != 3 || $sequencedStatus != 4)
								{
									my $updateClone=$dbh->prepare("UPDATE clones SET sequenced = ? WHERE name LIKE ? OR origin LIKE ?");
									$updateClone->execute($jobToSequence[3],$_,$_);
									my $updateFpcClone=$dbh->prepare("UPDATE matrix SET x = ? WHERE container LIKE 'fpcClone' AND name LIKE ?");
									$updateFpcClone->execute($jobToSequence[3],$_);
								}
							}
							$assignedSequenceNumber++;
							$bacIdAssigned = 1;
							print LOG "Good\n";
							last;
						}
						else
						{
							print LOG "Bad\n";
						}
					}
				}
				if($besTotalNumber > 0 && $bacIdAssigned < 1)
				{
					my $matchedBesNumber;
					open (CMD,"$blastn -query $tmpdir/$jobToSequence[0].seq -subject $tmpdir/$input.$$.bes -dust no -max_target_seqs 10000 -outfmt 6 |") or die "can't open CMD: $!";
					while(<CMD>)
					{
						my @blastLine = split /\t/, $_;
						next if ($blastLine[2] < $besMatchIdentity);
						next if ($blastLine[6] > 1000 && $blastLine[7] < $jobToSequence[5] - 1000); #determine ends location
						my ($bac,$besDirection)  = split /\./,$blastLine[1];
						$matchedBesNumber->{$bac}++;
					}
					close(CMD);
					for (sort { $matchedBesNumber->{$b} <=> $matchedBesNumber->{$a} } keys(%$matchedBesNumber))
					{
						print LOG "$jobToSequence[0]\t$_\tBES$cloneBesNumber->{$_}\t$matchedBesNumber->{$_}\t";
						if ($matchedBesNumber->{$_} > 0)
						{
							if($matchedBesNumber->{$_} >= $cloneBesNumber->{$_})
							{
								my $updateSequence=$dbh->prepare("UPDATE matrix SET name = ?, z = ?, barcode = 2 WHERE id = ?");
								$updateSequence->execute($_,$matchedBesNumber->{$_},$jobToSequence[0]);
							}
							else
							{
								#this condition needs to be updated
								my $updateSequence=$dbh->prepare("UPDATE matrix SET name = ?, z = ?, barcode = 2 WHERE id = ?");
								$updateSequence->execute($_,$matchedBesNumber->{$_},$jobToSequence[0]);
							}
							my $sequencedStatus = 0;
							my $getSequenced = $dbh->prepare("SELECT * FROM clones WHERE name LIKE ? OR origin LIKE ?");
							$getSequenced->execute($_,$_);
							while (my @getSequenced = $getSequenced->fetchrow_array())
							{
								$sequencedStatus = $getSequenced[6];
							}
							if ($jobToSequence[3] == 1 || $jobToSequence[3] == 2)
							{
								my $updateClone=$dbh->prepare("UPDATE clones SET sequenced = ? WHERE name LIKE ? OR origin LIKE ?");
								$updateClone->execute($jobToSequence[3],$_,$_);
								my $updateFpcClone=$dbh->prepare("UPDATE matrix SET x = ? WHERE container LIKE 'fpcClone' AND name LIKE ?");
								$updateFpcClone->execute($jobToSequence[3],$_);
							}
							elsif($jobToSequence[3] == 3)
							{
								if($sequencedStatus != 1 || $sequencedStatus != 2)
								{
									my $updateClone=$dbh->prepare("UPDATE clones SET sequenced = ? WHERE name LIKE ? OR origin LIKE ?");
									$updateClone->execute($jobToSequence[3],$_,$_);
									my $updateFpcClone=$dbh->prepare("UPDATE matrix SET x = ? WHERE container LIKE 'fpcClone' AND name LIKE ?");
									$updateFpcClone->execute($jobToSequence[3],$_);
								}
							}
							elsif($jobToSequence[3] == 4)
							{
								if($sequencedStatus != 1 || $sequencedStatus != 2 || $sequencedStatus != 3)
								{
									my $updateClone=$dbh->prepare("UPDATE clones SET sequenced = ? WHERE name LIKE ? OR origin LIKE ?");
									$updateClone->execute($jobToSequence[3],$_,$_);
									my $updateFpcClone=$dbh->prepare("UPDATE matrix SET x = ? WHERE container LIKE 'fpcClone' AND name LIKE ?");
									$updateFpcClone->execute($jobToSequence[3],$_);
								}
							}
							else
							{
								if($sequencedStatus != 1 || $sequencedStatus != 2 || $sequencedStatus != 3 || $sequencedStatus != 4)
								{
									my $updateClone=$dbh->prepare("UPDATE clones SET sequenced = ? WHERE name LIKE ? OR origin LIKE ?");
									$updateClone->execute($jobToSequence[3],$_,$_);
									my $updateFpcClone=$dbh->prepare("UPDATE matrix SET x = ? WHERE container LIKE 'fpcClone' AND name LIKE ?");
									$updateFpcClone->execute($jobToSequence[3],$_);
								}
							}
							$assignedSequenceNumber++;
							print LOG "Good\n";
							last;
						}
						else
						{
							print LOG "Bad\n";
						}
					}
				}
				unlink ("$tmpdir/$jobToSequence[0].seq");
			}
			unlink ("$tmpdir/$input.$$.bes");
			unlink ("$tmpdir/$input.$$.tag");
		}
		my $updateJob=$dbh->do("UPDATE matrix SET barcode = $assignedSequenceNumber WHERE container LIKE 'job' AND (name LIKE '$input' OR name LIKE '-$input')");
		close(LOG);
	}
	exit 0;
}
else{
	die "couldn't fork: $!\n";
}
