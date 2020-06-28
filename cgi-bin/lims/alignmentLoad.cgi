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

my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);

my $queryGenomeId = param ('queryGenomeId') || '';
my $subjectGenomeId = param ('subjectGenomeId') || '';
my $alignEngine = param ('alignEngine') || 'blastn';
my $alignmentFile = upload ('alignmentFile');
my $alignmentFilePath = param ('alignmentFilePath') || '';
my $alignmentInfile = "$tmpdir/$$.tabular";

print header;

if($queryGenomeId && $subjectGenomeId && ($alignmentFile || $alignmentFilePath))
{
	my $pid = fork();
	if ($pid) {
		print <<END;
<script>
	parent.closeDialog();
	parent.errorPop("It's being loaded! This processing might take a while.");
</script>
END
	}
	elsif($pid == 0){
		if($alignmentFilePath)
		{
			#$alignmentInfile = $alignmentFilePath;
			`cp $alignmentFilePath $alignmentInfile`;
		}
		else
		{
			open (FILE, ">$alignmentInfile");
			while (read ($alignmentFile, my $Buffer, 1024)) {
				print FILE $Buffer;
			}
			close FILE;
		}
		`perl -p -i -e 's/\r/\n/g' $alignmentInfile`; #convert CR line terminators (MAC OS) into LF line terminators (Unix)
		close (STDOUT);
		#connect to the mysql server
		my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);

		my $queryId;
		my $queryGenome=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
		$queryGenome->execute($queryGenomeId);
		my @queryGenome = $queryGenome->fetchrow_array();
		if($queryGenome[1] eq 'library')
		{
			my $getClones = $dbh->prepare("SELECT * FROM clones WHERE sequenced > 0 AND libraryId = ?");
			$getClones->execute($queryGenomeId);
			while(my @getClones = $getClones->fetchrow_array())
			{
				my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o < 50 AND name LIKE ?");
				$getSequences->execute($getClones[1]);
				while(my @getSequences = $getSequences->fetchrow_array())
				{
					$queryId->{$getSequences[2]} = $getSequences[0];
				}
			}
		}
		if($queryGenome[1] eq 'genome')
		{
			my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o = 99 AND x = ?");
			$getSequences->execute($queryGenomeId);
			while(my @getSequences = $getSequences->fetchrow_array())
			{
				$queryId->{$getSequences[2]} = $getSequences[0];
			}
		}

		my $subjectId;
		if ($queryGenomeId eq $subjectGenomeId)
		{
			$subjectId = $queryId;
		}
		else
		{
			my $subjectGenome=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$subjectGenome->execute($subjectGenomeId);
			my @subjectGenome = $subjectGenome->fetchrow_array();
			if($subjectGenome[1] eq 'library')
			{
				my $getClones = $dbh->prepare("SELECT * FROM clones WHERE sequenced > 0 AND libraryId = ?");
				$getClones->execute($subjectGenomeId);
				while(my @getClones = $getClones->fetchrow_array())
				{
					my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o < 50 AND name LIKE ?");
					$getSequences->execute($getClones[1]);
					while(my @getSequences = $getSequences->fetchrow_array())
					{
						$subjectId->{$getSequences[2]} = $getSequences[0];
					}
				}
			}
			if($subjectGenome[1] eq 'genome')
			{
				my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o = 99 AND x = ?");
				$getSequences->execute($subjectGenomeId);
				while(my @getSequences = $getSequences->fetchrow_array())
				{
					$subjectId->{$getSequences[2]} = $getSequences[0];
				}
			}
		}

		open(ALN, "$alignmentInfile") or die "cannot open file $alignmentInfile";
		while(<ALN>)
		{
			/^#/ and next;
			my @hit = split("\t",$_);
			if (exists $queryId->{$hit[0]} && exists $subjectId->{$hit[1]})
			{
				$hit[0] = $queryId->{$hit[0]};
				$hit[1] = $subjectId->{$hit[1]};
				my $insertAlignmentA=$dbh->prepare("INSERT INTO alignment VALUES ('', '$alignEngine', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)");
				$insertAlignmentA->execute(@hit);

				#switch query and subject
				if($hit[8] < $hit[9])
				{
					my $exchange = $hit[8];
					$hit[8] = $hit[6];
					$hit[6] = $exchange;
					$exchange = $hit[9];
					$hit[9] = $hit[7];
					$hit[7] = $exchange;
					$exchange = $hit[1];
					$hit[1] = $hit[0];
					$hit[0] = $exchange;
				}
				else
				{
					my $exchange = $hit[8];
					$hit[8] = $hit[7];
					$hit[7] = $exchange;
					$exchange = $hit[9];
					$hit[9] = $hit[6];
					$hit[6] = $exchange;
					$exchange = $hit[1];
					$hit[1] = $hit[0];
					$hit[0] = $exchange;
				}
				my $insertAlignmentB=$dbh->prepare("INSERT INTO alignment VALUES ('', '$alignEngine', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)");
				$insertAlignmentB->execute(@hit);
			}
			else
			{
				next;
			}
		}
		close(ALN);
		unlink ($alignmentInfile);
	}
	else{
		die "couldn't fork: $!\n";
	}
}
else
{
	print <<END;
<script>
	parent.errorPop("Please provide required infomation or file!");
</script>
END
}
