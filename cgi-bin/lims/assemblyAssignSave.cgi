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

my $chrNumber = param ('chrNumber');
my @assemblyCtgId = param('assemblyCtgId');
my $position;
print header;

for my $assemblyCtgId(@assemblyCtgId)
{
	my $assemblyCtg=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$assemblyCtg->execute($assemblyCtgId);
	my @assemblyCtg = $assemblyCtg->fetchrow_array();
	my $assembly=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$assembly->execute($assemblyCtg[3]);
	my @assembly = $assembly->fetchrow_array();
	unless ($assembly[7] == 1 || $assembly[7] == 0) # exit if for frozen or running assembly
	{
		print <<END;
<script>
	parent.closeDialog();
	parent.errorPop("This assembly is running or frozen.");
</script>	
END
		exit;
	}

	if ($assembly[5])
	{
		if ($chrNumber == 0)
		{
			my $update=$dbh->do("UPDATE matrix SET x = 0, z = 0 WHERE id = $assemblyCtgId ");
		}
		else
		{
			my $genomeSeq=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o = 99 AND x = $assembly[5] AND z = ? ");
			$genomeSeq->execute($chrNumber);
			my @genomeSeq = $genomeSeq->fetchrow_array();
			my $maxAlign=0;
			$position=0;
			foreach (split ",", $assemblyCtg[8])
			{
				$_ =~ s/[^a-zA-Z0-9]//g;
				my $assemblySeq=$dbh->prepare ("SELECT * FROM matrix WHERE id = ?");
				$assemblySeq->execute($_);
				while (my @assemblySeq = $assemblySeq->fetchrow_array())
				{
					my $getAlignment=$dbh->prepare("SELECT * FROM alignment WHERE query =? AND subject = ? ");
					$getAlignment->execute($assemblySeq[5],$genomeSeq[0]);
					while(my @getAlignment = $getAlignment->fetchrow_array())
					{
						if ($assemblySeq[7] > 0)
						{
							my $pos1=$getAlignment[10] < $getAlignment[11] ? $getAlignment[10] : $getAlignment[11];
							my $pos2=$getAlignment[8] < $getAlignment[9] ? $getAlignment[8] : $getAlignment[9];
							$position=$pos1-$pos2 if ($maxAlign < $getAlignment[5]);
							$maxAlign=$maxAlign > $getAlignment[5] ? $maxAlign :$getAlignment[5];
						}
						else
						{
							my $pos1=$getAlignment[10] < $getAlignment[11] ? $getAlignment[10] : $getAlignment[11];
							my $pos2=$getAlignment[8] > $getAlignment[9] ? $getAlignment[8] : $getAlignment[9];
							$position=$pos1-$assemblySeq[6]+$pos2 if ($maxAlign < $getAlignment[5]);
							$maxAlign=$maxAlign > $getAlignment[5] ? $maxAlign :$getAlignment[5];
						}
					}
				}
			}
			my $update=$dbh->do("UPDATE matrix SET x = $chrNumber,z = $position WHERE id = $assemblyCtgId ");
		}
	}
	else
	{
		my $update=$dbh->do("UPDATE matrix SET x = $chrNumber WHERE id = $assemblyCtgId ");
	}
}
	print <<END;
<script>
	parent.closeDialog();
	parent.informationPop("Chromosome number assignment is done.");
	parent.refresh("menu");
</script>	
END



