#!/usr/bin/perl -w
use strict;
use CGI qw(:standard);
use CGI::Carp qw ( fatalsToBrowser );
use JSON::XS;
use DBI;
use lib "lib/";
use lib "lib/pangu";
use pangu;
use userCookie;

my $userCookie = new userCookie;
my $userId = (cookie('cid')) ? $userCookie->checkCookie(cookie('cid')) : 0;

print header();
if(!$userId)
{
	print <<eof;
	<h2>Error</h2>
	Please <a onclick="openDialog('login.cgi');">login</a> first!
	<script type="text/javascript">
		openDialog('login.cgi');
		loadingHide();
	</script>
eof
    exit;
}

my $commoncfg = readParam();
my $htdocs = $commoncfg->getProperty('HTDOCS');
my $dbuser = $commoncfg->getProperty('USERNAME');
my $dbpass = $commoncfg->getProperty('PASSWORD');
my $dbhost = $commoncfg->getProperty('DBHOST');
my $dbdata = $commoncfg->getProperty('DATABASE');
my $tmpdir = $commoncfg->getProperty('TMPDIR');
my $tempurl = $commoncfg->getProperty('TMPURL');

my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);

undef $/;# enable slurp mode
my $html = data();

my @itemId = param ('itemId');

my $itemNumber = scalar (@itemId);
if($itemNumber < 1)
{
	print 'Select at least 1 record first!';
	exit;
}

my $readyPhrase = ($itemNumber > 1) ? "$itemNumber selected records are ready for downloading." : "$itemNumber selected record is ready for downloading.";
open (RECORD,">$tmpdir/record.$$.txt") or die "can't open file: $tmpdir/record.$$.txt";
my $recordLineNumber = 0;
foreach (@itemId)
{
	my $item=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$item->execute($_);
	while (my @item = $item->fetchrow_array())
	{
		my $itemDetails = decode_json $item[8];
		unless ($recordLineNumber > 0)
		{
			my $column = 0;
			for (sort {$a <=> $b} keys %$itemDetails)
			{
				$itemDetails->{$_}->{'field'} = '' unless ($itemDetails->{$_}->{'field'});
				if ($column > 0)
				{
					print RECORD "\t$itemDetails->{$_}->{'field'}";
				}
				else
				{
					print RECORD "$itemDetails->{$_}->{'field'}";
				}
				$column++;
			}
			print RECORD "\n";
		}

		my $column = 0;
		for (sort {$a <=> $b} keys %$itemDetails)
		{
			$itemDetails->{$_}->{'value'} = '' unless ($itemDetails->{$_}->{'value'});
			if ($column > 0)
			{
				print RECORD "\t$itemDetails->{$_}->{'value'}";
			}
			else
			{
				print RECORD "$itemDetails->{$_}->{'value'}";
			}
			$column++;
		}
		print RECORD "\n";
	}
	$recordLineNumber++;
}
close (RECORD);
`gzip -f $tmpdir/record.$$.txt`;

$html =~ s/\$\$/$$/g;
$html =~ s/\$readyPhrase/$readyPhrase/g;
$html =~ s/\$tempurl/$tempurl/g;

print $html;

sub data{
my $data=<<'HTML';
$readyPhrase
<script>
$('#dialog').dialog("option", "title", "Download Records");
$( "#dialog" ).dialog( "option", "buttons", [ { text: "Download", click: function() { location.href='$tempurl/record.$$.txt.gz'; } }, { text: "OK", click: function() {closeDialog(); } } ] );
</script>
HTML
return $data;}
