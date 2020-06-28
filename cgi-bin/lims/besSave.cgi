#!/usr/bin/perl -w
use strict;
use CGI qw(:standard);
use CGI::Carp qw ( fatalsToBrowser );
use JSON::XS;
use DBI;
use Bio::SeqIO;
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

my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);
my $libraryId = param ('libraryId') || '';
my $besFile = upload ('besFile');
my $besFilePath = param ('besFilePath') || '';
my $replace = param ('replace') || '0';
my $infile = "$tmpdir/$$.bes";
my $seqDir;
$seqDir->{'NA'} = 0;
$seqDir->{'f'} = 1;
$seqDir->{'r'} = 2;

print header;

if($besFile || $besFilePath)
{
	my $pid = fork();
	if ($pid) {
		print <<END;
<script>
parent.closeDialog();
parent.refresh("menu");
</script>
END
	}
	elsif($pid == 0){
		close (STDOUT);
		if($besFilePath)
		{
			$infile = $besFilePath;
		}
		else
		{
			open (FILE, ">$infile");
			while (read ($besFile, my $Buffer, 1024)) {
				print FILE $Buffer;
			}
			close FILE;
		}
		my $library=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
		$library->execute($libraryId);
		my @library = $library->fetchrow_array();
		if($replace > 0)
		{
			my $deleteBes=$dbh->do("DELETE FROM matrix WHERE container LIKE 'sequence' AND o = 98 AND x = $libraryId");
		}
		#loading sequence
		my $in = Bio::SeqIO->new(-file => $infile,
								-format => 'Fasta');
		while ( my $seq = $in->next_seq() )
		{
			my $seqDetails;
			$seqDetails->{'id'} = $seq->id;
			$seqDetails->{'description'} = $seq->desc || '';
			$seqDetails->{'sequence'} = $seq->seq;
			$seqDetails->{'sequence'} =~ tr/a-zA-Z/N/c; #replace nonword characters.
			$seqDetails->{'gapList'} = '';
			my $cloneName = $seq->id;
			my $seqDirNumber = 0;
			if($cloneName =~ /(.+)\.(.*)$/)
			{
				$seqDirNumber = $seqDir->{$2};
				$cloneName = $1;
			}
			$cloneName =~ /(\d+)(\D+)(\d+)$/;
			my $plateName =  sprintf "%0*d", 4, $1;
			my $row =  uc $2;
			my $col =  sprintf "%0*d", 2, $3;
			$cloneName = "$library[2]$plateName$row$col";
			my $seqLength = $seq->length();
			my $json = JSON::XS->new->allow_nonref;
			my $seqDetailsEncoded = $json->encode($seqDetails);
			my $insertSequence=$dbh->prepare("INSERT INTO matrix VALUES (0, 'sequence', ?, 98, ?, ?, ?, 0, ?, ?, NOW())");
			$insertSequence->execute($cloneName,$libraryId,$seqLength,$seqDirNumber,$seqDetailsEncoded,$userName);
		}
		unlink ($infile) if (!$besFilePath);
		exit 0;
	}
	else{
		die "couldn't fork: $!\n";
	}
}
else
{
	print <<END;
<script>
	parent.errorPop("No BES file found!");
</script>
END
	exit;
}
