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
exit if (!$userId);

my $commoncfg = readParam();
my $htdocs = $commoncfg->getProperty('HTDOCS');
my $dbuser = $commoncfg->getProperty('USERNAME');
my $dbpass = $commoncfg->getProperty('PASSWORD');
my $dbhost = $commoncfg->getProperty('DBHOST');
my $dbdata = $commoncfg->getProperty('DATABASE');

my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);

my $seqId = param ('seqId') || '';

my $sequence = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
$sequence->execute($seqId);
my @sequence=$sequence->fetchrow_array();
my $sequenceDetails = decode_json $sequence[8];
$sequenceDetails->{'filter'} = '' unless (exists $sequenceDetails->{'filter'});

print header;
print <<END;
<input class='ui-widget-content ui-corner-all' name="filter" id="editSeqFilter" size="32" type="text" maxlength="32" value="$sequenceDetails->{'filter'}"  placeholder="Sequence Filter" onBlur="loaddiv('seqFilter$seqId','seqFilterSave.cgi?seqId=$seqId&filter='+this.value)"/>
END
