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

my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);

my $assemblyCtgId = param ('assemblyCtgId') || '';
my $alignmentId = param ('alignmentId') || '';
my $scrollLeft = param ('scrollLeft') || '0';

print header;

if($assemblyCtgId)
{
	my $checkAssemblyCtg = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$checkAssemblyCtg->execute($assemblyCtgId);
	if($checkAssemblyCtg->rows < 1)
	{
		print <<END;
<script>
	errorPop("Not a valid operation!");
</script>	
END
	}
	else
	{
		my @checkAssemblyCtg = $checkAssemblyCtg->fetchrow_array();
		my @seqInCtg;
		my %seqInCtg;
		foreach (split ",", $checkAssemblyCtg[8])
		{
			/^-/ and next;
			$_ =~ s/[^a-zA-Z0-9]//g;
			push @seqInCtg,$_;

			my $assemblySeqs = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$assemblySeqs->execute($_);
			while(my @assemblySeqs = $assemblySeqs->fetchrow_array())
			{
				$seqInCtg{$assemblySeqs[5]} = $assemblySeqs[0]; #sequenceId -> assemblySeqId
			}
		}
		my $totalSeqInCtg = @seqInCtg;

		if($alignmentId)
		{
			my $getAlignment = $dbh->prepare("SELECT * FROM alignment WHERE id = ?");
			$getAlignment->execute($alignmentId);
			my @getAlignment = $getAlignment->fetchrow_array();
			
			my $assemblyPreSeq=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$assemblyPreSeq->execute($seqInCtg{$getAlignment[2]});
			my @assemblyPreSeq = $assemblyPreSeq->fetchrow_array();
			my $preSeqStart;
			my $preSeqEnd;
			if($assemblyPreSeq[8])
			{
				($preSeqStart,$preSeqEnd) = split ",",$assemblyPreSeq[8];
			}
			else
			{
				$preSeqStart = 1;
				$preSeqEnd = $assemblyPreSeq[6];
			}
			my $preSequence = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$preSequence->execute($getAlignment[2]);
			my @preSequence = $preSequence->fetchrow_array();

			my $assemblyNextSeq=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$assemblyNextSeq->execute($seqInCtg{$getAlignment[3]});
			my @assemblyNextSeq = $assemblyNextSeq->fetchrow_array();
			my $nextSeqStart;
			my $nextSeqEnd;
			if($assemblyNextSeq[8])
			{
				($nextSeqStart,$nextSeqEnd) = split ",",$assemblyNextSeq[8];
			}
			else
			{
				$nextSeqStart = 1;
				$nextSeqEnd = $assemblyNextSeq[6];
			}
			my $nextSequence = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$nextSequence->execute($getAlignment[3]);
			my @nextSequence = $nextSequence->fetchrow_array();

			my $preSeqStartCandidate = $preSeqStart;
			my $preSeqEndCandidate = $preSeqEnd;
			my $nextSeqStartCandidate = $nextSeqStart;
			my $nextSeqEndCandidate = $nextSeqEnd;

			if($preSequence[3] < 4) #if preSeq has non-gapped sequence
			{
				#keep preSeq sequence
				if($assemblyPreSeq[7] > 0)
				{
					if ($getAlignment[10] < $getAlignment[11])
					{
						$preSeqEndCandidate = $getAlignment[9];
						$nextSeqStartCandidate = $getAlignment[11] + 1;
					}
					else
					{
						$preSeqEndCandidate = $getAlignment[9];
						$nextSeqEndCandidate = $getAlignment[11] - 1;
					}
				}
				else
				{
					if ($getAlignment[10] < $getAlignment[11])
					{
						$preSeqStartCandidate = $getAlignment[8];
						$nextSeqEndCandidate = $getAlignment[10] - 1;
					}
					else
					{
						$preSeqStartCandidate = $getAlignment[8];
						$nextSeqStartCandidate = $getAlignment[10] + 1;
					}
				}

				if ($preSeqStartCandidate >= 1 && $preSeqEndCandidate <= $assemblyPreSeq[6] && $nextSeqStartCandidate >= 1 && $nextSeqEndCandidate <= $assemblyNextSeq[6] && $preSeqStartCandidate <= $preSeqEndCandidate && $nextSeqStartCandidate <= $nextSeqEndCandidate)
				{
					my $updateAssemblySeqPre=$dbh->do("UPDATE matrix SET note = '$preSeqStartCandidate,$preSeqEndCandidate' WHERE id = $assemblyPreSeq[0]");
					my $updateAssemblySeqNext=$dbh->do("UPDATE matrix SET note = '$nextSeqStartCandidate,$nextSeqEndCandidate' WHERE id = $assemblyNextSeq[0]");
				}
				else
				{
					#keep nextSeq sequence
					$preSeqStartCandidate = $preSeqStart;
					$preSeqEndCandidate = $preSeqEnd;
					$nextSeqStartCandidate = $nextSeqStart;
					$nextSeqEndCandidate = $nextSeqEnd;
					if($assemblyPreSeq[7] > 0)
					{
						if ($getAlignment[10] < $getAlignment[11])
						{
							$preSeqEndCandidate = $getAlignment[8] - 1;
							$nextSeqStartCandidate = $getAlignment[10];
						}
						else
						{
							$preSeqEndCandidate = $getAlignment[8] - 1;
							$nextSeqEndCandidate = $getAlignment[10];
						}
					}
					else
					{
						if ($getAlignment[10] < $getAlignment[11])
						{
							$preSeqStartCandidate = $getAlignment[9] + 1;
							$nextSeqEndCandidate = $getAlignment[11];
						}
						else
						{
							$preSeqStartCandidate = $getAlignment[9] + 1;
							$nextSeqStartCandidate = $getAlignment[11];
						}
					}

					if ($preSeqStartCandidate >= 1 && $preSeqEndCandidate <= $assemblyPreSeq[6] && $nextSeqStartCandidate >= 1 && $nextSeqEndCandidate <= $assemblyNextSeq[6] && $preSeqStartCandidate <= $preSeqEndCandidate && $nextSeqStartCandidate <= $nextSeqEndCandidate)
					{
						my $updateAssemblySeqPre=$dbh->do("UPDATE matrix SET note = '$preSeqStartCandidate,$preSeqEndCandidate' WHERE id = $assemblyPreSeq[0]");
						my $updateAssemblySeqNext=$dbh->do("UPDATE matrix SET note = '$nextSeqStartCandidate,$nextSeqEndCandidate' WHERE id = $assemblyNextSeq[0]");
					}
					else
					{
						print <<END;
<script>
	errorPop("A conflict region found, filtering action cancelled!");
</script>
END
						exit;
					}
				}
			}
			else
			{
				#keep nextSeq sequence
				if($assemblyPreSeq[7] > 0)
				{
					if ($getAlignment[10] < $getAlignment[11])
					{
						$preSeqEndCandidate = $getAlignment[8] - 1;
						$nextSeqStartCandidate = $getAlignment[10];
					}
					else
					{
						$preSeqEndCandidate = $getAlignment[8] - 1;
						$nextSeqEndCandidate = $getAlignment[10];
					}
				}
				else
				{
					if ($getAlignment[10] < $getAlignment[11])
					{
						$preSeqStartCandidate = $getAlignment[9] + 1;
						$nextSeqEndCandidate = $getAlignment[11];
					}
					else
					{
						$preSeqStartCandidate = $getAlignment[9] + 1;
						$nextSeqStartCandidate = $getAlignment[11];
					}
				}

				if ($preSeqStartCandidate >= 1 && $preSeqEndCandidate <= $assemblyPreSeq[6] && $nextSeqStartCandidate >= 1 && $nextSeqEndCandidate <= $assemblyNextSeq[6] && $preSeqStartCandidate <= $preSeqEndCandidate && $nextSeqStartCandidate <= $nextSeqEndCandidate)
				{
					my $updateAssemblySeqPre=$dbh->do("UPDATE matrix SET note = '$preSeqStartCandidate,$preSeqEndCandidate' WHERE id = $assemblyPreSeq[0]");
					my $updateAssemblySeqNext=$dbh->do("UPDATE matrix SET note = '$nextSeqStartCandidate,$nextSeqEndCandidate' WHERE id = $assemblyNextSeq[0]");
				}
				else
				{
					$preSeqStartCandidate = $preSeqStart;
					$preSeqEndCandidate = $preSeqEnd;
					$nextSeqStartCandidate = $nextSeqStart;
					$nextSeqEndCandidate = $nextSeqEnd;
					#keep preSeq sequence
					if($assemblyPreSeq[7] > 0)
					{
						if ($getAlignment[10] < $getAlignment[11])
						{
							$preSeqEndCandidate = $getAlignment[9];
							$nextSeqStartCandidate = $getAlignment[11] + 1;
						}
						else
						{
							$preSeqEndCandidate = $getAlignment[9];
							$nextSeqEndCandidate = $getAlignment[11] - 1;
						}
					}
					else
					{
						if ($getAlignment[10] < $getAlignment[11])
						{
							$preSeqStartCandidate = $getAlignment[8];
							$nextSeqEndCandidate = $getAlignment[10] - 1;
						}
						else
						{
							$preSeqStartCandidate = $getAlignment[8];
							$nextSeqStartCandidate = $getAlignment[10] + 1;
						}
					}

					if ($preSeqStartCandidate >= 1 && $preSeqEndCandidate <= $assemblyPreSeq[6] && $nextSeqStartCandidate >= 1 && $nextSeqEndCandidate <= $assemblyNextSeq[6] && $preSeqStartCandidate <= $preSeqEndCandidate && $nextSeqStartCandidate <= $nextSeqEndCandidate)
					{
						my $updateAssemblySeqPre=$dbh->do("UPDATE matrix SET note = '$preSeqStartCandidate,$preSeqEndCandidate' WHERE id = $assemblyPreSeq[0]");
						my $updateAssemblySeqNext=$dbh->do("UPDATE matrix SET note = '$nextSeqStartCandidate,$nextSeqEndCandidate' WHERE id = $assemblyNextSeq[0]");
					}
					else
					{
						print <<END;
<script>
	errorPop("A conflict region found, filtering action cancelled!");
</script>
END
						exit;
					}
				}
			}
		}
		else
		{
			for (@seqInCtg)
			{
				my $assemblySeqResetLength=$dbh->do("UPDATE matrix SET note = CONCAT('1,', z) WHERE id = $_");
			}
			for (my $i = 1; $i < $totalSeqInCtg; $i++)
			{
				my $assemblyPreSeq=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
				$assemblyPreSeq->execute($seqInCtg[$i-1]);
				my @assemblyPreSeq = $assemblyPreSeq->fetchrow_array();
				my $preSeqStart;
				my $preSeqEnd;
				if($assemblyPreSeq[8])
				{
					($preSeqStart,$preSeqEnd) = split ",",$assemblyPreSeq[8];
				}
				else
				{
					$preSeqStart = 1;
					$preSeqEnd = $assemblyPreSeq[6];
				}
				my $preSequence = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
				$preSequence->execute($assemblyPreSeq[5]);
				my @preSequence = $preSequence->fetchrow_array();

				my $assemblyNextSeq=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
				$assemblyNextSeq->execute($seqInCtg[$i]);
				my @assemblyNextSeq = $assemblyNextSeq->fetchrow_array();
				my $nextSeqStart;
				my $nextSeqEnd;
				if($assemblyNextSeq[8])
				{
					($nextSeqStart,$nextSeqEnd) = split ",",$assemblyNextSeq[8];
				}
				else
				{
					$nextSeqStart = 1;
					$nextSeqEnd = $assemblyNextSeq[6];
				}
				my $nextSequence = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
				$nextSequence->execute($assemblyNextSeq[5]);
				my @nextSequence = $nextSequence->fetchrow_array();

				my $getAlignment = $dbh->prepare("SELECT * FROM alignment WHERE query = ? AND subject = ? ORDER BY id LIMIT 1");
				$getAlignment->execute($assemblyPreSeq[5],$assemblyNextSeq[5]);
				my @getAlignment = $getAlignment->fetchrow_array();

				my $preSeqStartCandidate = $preSeqStart;
				my $preSeqEndCandidate = $preSeqEnd;
				my $nextSeqStartCandidate = $nextSeqStart;
				my $nextSeqEndCandidate = $nextSeqEnd;

				if($preSequence[3] < 4) #if preSeq has non-gapped sequence
				{
					#keep preSeq sequence
					if($assemblyPreSeq[7] > 0)
					{
						if ($getAlignment[10] < $getAlignment[11])
						{
							$preSeqEndCandidate = $getAlignment[9];
							$nextSeqStartCandidate = $getAlignment[11] + 1;
						}
						else
						{
							$preSeqEndCandidate = $getAlignment[9];
							$nextSeqEndCandidate = $getAlignment[11] - 1;
						}
					}
					else
					{
						if ($getAlignment[10] < $getAlignment[11])
						{
							$preSeqStartCandidate = $getAlignment[8];
							$nextSeqEndCandidate = $getAlignment[10] - 1;
						}
						else
						{
							$preSeqStartCandidate = $getAlignment[8];
							$nextSeqStartCandidate = $getAlignment[10] + 1;
						}
					}

					if ($preSeqStartCandidate >= 1 && $preSeqEndCandidate <= $assemblyPreSeq[6] && $nextSeqStartCandidate >= 1 && $nextSeqEndCandidate <= $assemblyNextSeq[6] && $preSeqStartCandidate <= $preSeqEndCandidate && $nextSeqStartCandidate <= $nextSeqEndCandidate)
					{
						my $updateAssemblySeqPre=$dbh->do("UPDATE matrix SET note = '$preSeqStartCandidate,$preSeqEndCandidate' WHERE id = $assemblyPreSeq[0]");
						my $updateAssemblySeqNext=$dbh->do("UPDATE matrix SET note = '$nextSeqStartCandidate,$nextSeqEndCandidate' WHERE id = $assemblyNextSeq[0]");
					}
					else
					{
						#keep nextSeq sequence
						$preSeqStartCandidate = $preSeqStart;
						$preSeqEndCandidate = $preSeqEnd;
						$nextSeqStartCandidate = $nextSeqStart;
						$nextSeqEndCandidate = $nextSeqEnd;
						if($assemblyPreSeq[7] > 0)
						{
							if ($getAlignment[10] < $getAlignment[11])
							{
								$preSeqEndCandidate = $getAlignment[8] - 1;
								$nextSeqStartCandidate = $getAlignment[10];
							}
							else
							{
								$preSeqEndCandidate = $getAlignment[8] - 1;
								$nextSeqEndCandidate = $getAlignment[10];
							}
						}
						else
						{
							if ($getAlignment[10] < $getAlignment[11])
							{
								$preSeqStartCandidate = $getAlignment[9] + 1;
								$nextSeqEndCandidate = $getAlignment[11];
							}
							else
							{
								$preSeqStartCandidate = $getAlignment[9] + 1;
								$nextSeqStartCandidate = $getAlignment[11];
							}
						}

						if ($preSeqStartCandidate >= 1 && $preSeqEndCandidate <= $assemblyPreSeq[6] && $nextSeqStartCandidate >= 1 && $nextSeqEndCandidate <= $assemblyNextSeq[6] && $preSeqStartCandidate <= $preSeqEndCandidate && $nextSeqStartCandidate <= $nextSeqEndCandidate)
						{
							my $updateAssemblySeqPre=$dbh->do("UPDATE matrix SET note = '$preSeqStartCandidate,$preSeqEndCandidate' WHERE id = $assemblyPreSeq[0]");
							my $updateAssemblySeqNext=$dbh->do("UPDATE matrix SET note = '$nextSeqStartCandidate,$nextSeqEndCandidate' WHERE id = $assemblyNextSeq[0]");
						}
						else
						{
							print <<END;
	<script>
		errorPop("A conflict region found, filtering action cancelled!");
	</script>
END
							exit;
						}
					}
				}
				else
				{
					#keep nextSeq sequence
					if($assemblyPreSeq[7] > 0)
					{
						if ($getAlignment[10] < $getAlignment[11])
						{
							$preSeqEndCandidate = $getAlignment[8] - 1;
							$nextSeqStartCandidate = $getAlignment[10];
						}
						else
						{
							$preSeqEndCandidate = $getAlignment[8] - 1;
							$nextSeqEndCandidate = $getAlignment[10];
						}
					}
					else
					{
						if ($getAlignment[10] < $getAlignment[11])
						{
							$preSeqStartCandidate = $getAlignment[9] + 1;
							$nextSeqEndCandidate = $getAlignment[11];
						}
						else
						{
							$preSeqStartCandidate = $getAlignment[9] + 1;
							$nextSeqStartCandidate = $getAlignment[11];
						}
					}

					if ($preSeqStartCandidate >= 1 && $preSeqEndCandidate <= $assemblyPreSeq[6] && $nextSeqStartCandidate >= 1 && $nextSeqEndCandidate <= $assemblyNextSeq[6] && $preSeqStartCandidate <= $preSeqEndCandidate && $nextSeqStartCandidate <= $nextSeqEndCandidate)
					{
						my $updateAssemblySeqPre=$dbh->do("UPDATE matrix SET note = '$preSeqStartCandidate,$preSeqEndCandidate' WHERE id = $assemblyPreSeq[0]");
						my $updateAssemblySeqNext=$dbh->do("UPDATE matrix SET note = '$nextSeqStartCandidate,$nextSeqEndCandidate' WHERE id = $assemblyNextSeq[0]");
					}
					else
					{
						$preSeqStartCandidate = $preSeqStart;
						$preSeqEndCandidate = $preSeqEnd;
						$nextSeqStartCandidate = $nextSeqStart;
						$nextSeqEndCandidate = $nextSeqEnd;
						#keep preSeq sequence
						if($assemblyPreSeq[7] > 0)
						{
							if ($getAlignment[10] < $getAlignment[11])
							{
								$preSeqEndCandidate = $getAlignment[9];
								$nextSeqStartCandidate = $getAlignment[11] + 1;
							}
							else
							{
								$preSeqEndCandidate = $getAlignment[9];
								$nextSeqEndCandidate = $getAlignment[11] - 1;
							}
						}
						else
						{
							if ($getAlignment[10] < $getAlignment[11])
							{
								$preSeqStartCandidate = $getAlignment[8];
								$nextSeqEndCandidate = $getAlignment[10] - 1;
							}
							else
							{
								$preSeqStartCandidate = $getAlignment[8];
								$nextSeqStartCandidate = $getAlignment[10] + 1;
							}
						}

						if ($preSeqStartCandidate >= 1 && $preSeqEndCandidate <= $assemblyPreSeq[6] && $nextSeqStartCandidate >= 1 && $nextSeqEndCandidate <= $assemblyNextSeq[6] && $preSeqStartCandidate <= $preSeqEndCandidate && $nextSeqStartCandidate <= $nextSeqEndCandidate)
						{
							my $updateAssemblySeqPre=$dbh->do("UPDATE matrix SET note = '$preSeqStartCandidate,$preSeqEndCandidate' WHERE id = $assemblyPreSeq[0]");
							my $updateAssemblySeqNext=$dbh->do("UPDATE matrix SET note = '$nextSeqStartCandidate,$nextSeqEndCandidate' WHERE id = $assemblyNextSeq[0]");
						}
						else
						{
							print <<END;
	<script>
		errorPop("A conflict region found, filtering action cancelled!");
	</script>
END
							exit;
						}
					}
				}
			}
		}

		#update Ctg length
		my $assemblyCtgLength = 0;
		foreach (@seqInCtg)
		{
			my $assemblySeqList=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$assemblySeqList->execute($_);
			my @assemblySeqList = $assemblySeqList->fetchrow_array();
			my $assemblySeqStart;
			my $assemblySeqEnd;
			if($assemblySeqList[8])
			{
				($assemblySeqStart,$assemblySeqEnd) = split ",",$assemblySeqList[8];
			}
			else
			{
				$assemblySeqStart = 1;
				$assemblySeqEnd = $assemblySeqList[6];
				my $updateAssemblySeq=$dbh->do("UPDATE matrix SET note = '$assemblySeqStart,$assemblySeqEnd' WHERE id = $assemblySeqList[0]");
			}
			$assemblyCtgLength += $assemblySeqEnd - $assemblySeqStart + 1;
		}
		my $updateAssemblyCtgLength=$dbh->do("UPDATE matrix SET barcode = $assemblyCtgLength WHERE id = $checkAssemblyCtg[0]");

		print <<END;
<script>
closeViewer();
openViewer("assemblyCtgView.cgi?assemblyCtgId=$assemblyCtgId&scrollLeft=$scrollLeft");
</script>	
END
	}
}
else
{
	print <<END;
<script>
	errorPop("Not a valid operation!");
</script>	
END
}