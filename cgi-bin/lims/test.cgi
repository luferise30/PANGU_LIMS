#!/usr/bin/perl

use strict;
use warnings;
use CGI qw(:standard);
use pangu;
use DBI;

my $list=`ls -lrt`;
my $pwd=`pwd`;
my $cat=`cat main.conf`;
print header;

my $commoncfg = readParam();
my $htdocs = $commoncfg->getProperty('HTDOCS');
my $dbuser = $commoncfg->getProperty('USERNAME');
my $dbpass = $commoncfg->getProperty('PASSWORD');
my $dbhost = $commoncfg->getProperty('DBHOST');
my $dbdata = $commoncfg->getProperty('DATABASE');


my $dbuser = $commoncfg->getProperty('USERNAME');
my $dbpass = $commoncfg->getProperty('PASSWORD');
my $dbhost = $commoncfg->getProperty('DBHOST');
my $dbdata = $commoncfg->getProperty('DATABASE');
my $dbhtdocs = $commoncfg->getProperty('HTDOCS');

#my $dbh=DBI->connect("DBI:mysql:$commoncfg{'DATABASE'}:$commoncfg{'DBHOST'}",$commoncfg{'USERNAME'},$commoncfg{'PASSWORD'});
my $dbh=DBI->connect("DBI:mysql:$dbdata:$dbhost",$dbuser,$dbpass);

print header;
#print "Content-type: text/html\n\n";
print "<html>\n<body>\n";
print "<div style=\"width:100%; font-size:40px; font-weight:bold; text-align:center;\">";
my $a = 0;
&number();

print "</div>\n</body>\n</html>";
print "<pre>".$list."</pre>";
print "<pre>".$pwd."</pre>";
print "<pre>Username: ".$dbuser."</pre>";
print "<pre>Password: ".$dbpass."</pre>";
print "<pre>Database: ".$dbdata."</pre>";
print "<pre>Host: ".$dbhost."</pre>";
print "<pre>Htdocs: ".$dbhtdocs."</pre>";

sub number {
    $a++;
    print "number \$a = $a";
}
