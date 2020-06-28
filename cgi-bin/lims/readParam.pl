#!/usr/bin/perl -w

use strict;
use Config::Properties;

open my $cfh, '<', './main.conf' or die "unable to open property file";
#open(FI,'<','main.conf');

my $properties = Config::Properties->new();
$properties->load($cfh);
my $dbuser = $properties->getProperty('USERNAME');
my $dbpass = $properties->getProperty('PASSWORD');
my $dbhost = $properties->getProperty('DBHOST');
my $dbdata = $properties->getProperty('DATABASE');

print $dbuser." ".$dbpass." ".$dbhost." ".$dbdata."\n";

=cut
my @param = <FI>;
my %keyval=();

foreach my $param(@param){
    chomp($param);
    if ($param=~/=/){
       $param =~ /(\w+)\s*=\s*([\w\/:\.\_\-\*]+)\s*/g;
       my $key = $1;
       my $value = $2;
       #print $param."\n";
       if (defined($1) and defined($2)){
          #print $key." ".$value."\n";
          $keyval{$key}=$value;
       }
    }
}
foreach my $keys(sort(keys(%keyval))){
    print $keys."\t".$keyval{$keys}."\n";
}
=pod
