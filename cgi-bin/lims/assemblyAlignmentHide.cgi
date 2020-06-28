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

my $alignmentId = param ('alignmentId') || '';
my $assemblyId = param ('assemblyId') || '';
my $assemblyCtgId = param ('assemblyCtgId') || '';
my $openAssemblyId = param ('openAssemblyId') || '';
my $chr = param ('chr') || '0';
my $scrollLeft = param ('scrollLeft') || '0';

print header;

if($alignmentId)
{
	my $updateAlignment=$dbh->do("UPDATE alignment SET hidden = 1 WHERE id = $alignmentId");
	if($openAssemblyId)
	{
			print <<END;
<script>
closeViewer();
openViewer("assemblyChrView.cgi?assemblyId=$openAssemblyId&chr=$chr&scrollLeft=$scrollLeft");
</script>	
END
	}
	else
	{
		if($chr)
		{
			print <<END;
<script>
closeViewer();
openViewer("assemblyChrView.cgi?assemblyId=$assemblyId&chr=$chr&scrollLeft=$scrollLeft");
</script>	
END
		}
		else
		{
			if($assemblyCtgId)
			{
			print <<END;
<script>
closeViewer();
openViewer("assemblyCtgView.cgi?assemblyCtgId=$assemblyCtgId&scrollLeft=$scrollLeft");
</script>	
END
			}
			else
			{
				print <<END;
<script>
	informationPop('Alignment is hidden now!');
</script>	
END
			}
		}
	}
}
else
{
	print <<END;
<script>
	errorPop('Not a valid operation!');
</script>	
END
}
