package Connection;
use strict;
use DBI;
use pangu;
my $oneTrueSelf;

sub instance {
	unless (defined $oneTrueSelf) {
		my $type = shift;
		my $this = {};
		my $commoncfg = readParam();
my $htdocs = $commoncfg->getProperty('HTDOCS');
my $dbuser = $commoncfg->getProperty('USERNAME');
my $dbpass = $commoncfg->getProperty('PASSWORD');
my $dbhost = $commoncfg->getProperty('DBHOST');
my $dbdata = $commoncfg->getProperty('DATABASE');

		$this->{_dbh} = DBI->connect("DBI:mysql:$dbdata:$dbhost", $dbuser, $dbpass);
		die "connect failed: " . DBI->errstr() unless $this->{_dbh};
		$oneTrueSelf = bless $this, $type;
	}
	return $oneTrueSelf;
}
sub dbh {
	my $self = shift;
	return $self->{_dbh};
}

1;
