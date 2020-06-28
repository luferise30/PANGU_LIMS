#!/usr/bin/perl -w
use strict;
use CGI qw(:standard);
use CGI::Carp qw ( fatalsToBrowser );
use DBI;
use lib "lib/";
use lib "lib/pangu";
use pangu;
my $commoncfg = readParam();
my $htdocs = $commoncfg->getProperty('HTDOCS');
my $dbuser = $commoncfg->getProperty('USERNAME');
my $dbpass = $commoncfg->getProperty('PASSWORD');
my $dbhost = $commoncfg->getProperty('DBHOST');
my $dbdata = $commoncfg->getProperty('DATABASE');
my $htmldir = $commoncfg->getProperty('HTMLDIR');

print header(-cookie=>cookie(-name=>'menu',-value=>0));

open (HOME, "$htmldir/home.html") or die "can't open HOME: $!";
while (<HOME>)
{
	print $_;
}
close (HOME);
