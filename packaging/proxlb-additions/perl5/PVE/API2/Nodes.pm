package PVE::API2::Nodes::Nodeinfo;

use strict;
use warnings;

use Digest::MD5;
use Digest::SHA;
use Filesys::Df;
use HTTP::Status qw(:constants);
use JSON;
use POSIX qw(LONG_MAX);
use Time::Local qw(timegm_nocheck);
use Socket;
use IO::Socket::SSL;

use PVE::API2Tools;
use PVE::APLInfo;
use PVE::AccessControl;
use PVE::Cluster qw(cfs_read_file);
use PVE::DataCenterConfig;
use PVE::Exception qw(raise raise_perm_exc raise_param_exc);
use PVE::Firewall;
use PVE::HA::Config;
use PVE::HA::Env::PVE2;
use PVE::INotify;
use PVE::JSONSchema qw(get_standard_option);
use PVE::LXC;
use PVE::NodeConfig;
use PVE::ProcFSTools;
use PVE::QemuConfig;
use PVE::QemuServer;
use PVE::RESTEnvironment qw(log_warn);
use PVE::RESTHandler;
use PVE::RPCEnvironment;
use PVE::RRD;
use PVE::Report;
use PVE::SafeSyslog;
use PVE::Storage;
use PVE::Tools qw(file_get_contents);
use PVE::pvecfg;

use PVE::API2::APT;
use PVE::API2::Capabilities;
use PVE::API2::Ceph;
use PVE::API2::Certificates;
use PVE::API2::Disks;
use PVE::API2::Firewall::Host;
use PVE::API2::Hardware;
use PVE::API2::LXC::Status;
use PVE::API2::LXC;
use PVE::API2::Network;
use PVE::API2::NodeConfig;
use PVE::API2::Qemu::CPU;
use PVE::API2::Qemu;
use PVE::API2::Replication;
use PVE::API2::Services;
use PVE::API2::Storage::Scan;
use PVE::API2::Storage::Status;
use PVE::API2::Subscription;
use PVE::API2::Tasks;
use PVE::API2::VZDump;

my $have_sdn;
eval {
    require PVE::API2::Network::SDN::Zones::Status;
    $have_sdn = 1;
};

use base qw(PVE::RESTHandler);

my $verify_command_item_desc = {
    description => "An array of objects describing endpoints, methods and arguments.",
    type => "array",
    items => {
	type => "object",
	properties => {
	    path => {
		description => "A relative path to an API endpoint on this node.",
		type => "string",
		optional => 0,
	    },
	    method => {
		description => "A method related to the API endpoint (GET, POST etc.).",
		type => "string",
		pattern => "(GET|POST|PUT|DELETE)",
		optional => 0,
	    },
	    args => {
		description => "A set of parameter names and their values.",
		type => "object",
		optional => 1,
	    },
	},
    }
};

PVE::JSONSchema::register_format('pve-command-batch', \&verify_command_batch);
sub verify_command_batch {
    my ($value, $noerr) = @_;
    my $commands = eval { decode_json($value); };

    return if $noerr && $@;
    die "commands param did not contain valid JSON: $@" if $@;

    eval { PVE::JSONSchema::validate($commands, $verify_command_item_desc) };

    return $commands if !$@;

    return if $noerr;
    die "commands is not a valid array of commands: $@";
}

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Qemu",
    path => 'qemu',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::LXC",
    path => 'lxc',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Ceph",
    path => 'ceph',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::VZDump",
    path => 'vzdump',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Services",
    path => 'services',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Subscription",
    path => 'subscription',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Network",
    path => 'network',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Tasks",
    path => 'tasks',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Storage::Scan",
    path => 'scan',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Hardware",
    path => 'hardware',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Capabilities",
    path => 'capabilities',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Storage::Status",
    path => 'storage',
});

__PACKAGE__->register_method ({
   subclass => "PVE::API2::Disks",
   path => 'disks',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::APT",
    path => 'apt',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Firewall::Host",
    path => 'firewall',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Replication",
    path => 'replication',
});

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Certificates",
    path => 'certificates',
});


__PACKAGE__->register_method ({
    subclass => "PVE::API2::NodeConfig",
    path => 'config',
});

if ($have_sdn) {
    __PACKAGE__->register_method ({
	subclass => "PVE::API2::Network::SDN::Zones::Status",
	path => 'sdn/zones',
    });

__PACKAGE__->register_method ({
    name => 'sdnindex',
    path => 'sdn',
    method => 'GET',
    permissions => { user => 'all' },
    description => "SDN index.",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	},
    },
    returns => {
	type => 'array',
	items => {
	    type => "object",
	    properties => {},
	},
	links => [ { rel => 'child', href => "{name}" } ],
    },
    code => sub {
	my ($param) = @_;

	my $result = [
	    { name => 'zones' },
	];
	return $result;
    }});
}

__PACKAGE__->register_method ({
    name => 'index',
    path => '',
    method => 'GET',
    permissions => { user => 'all' },
    description => "Node index.",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	},
    },
    returns => {
	type => 'array',
	items => {
	    type => "object",
	    properties => {},
	},
	links => [ { rel => 'child', href => "{name}" } ],
    },
    code => sub {
	my ($param) = @_;

	my $result = [
	    { name => 'aplinfo' },
	    { name => 'apt' },
	    { name => 'capabilities' },
	    { name => 'ceph' },
	    { name => 'certificates' },
	    { name => 'config' },
	    { name => 'disks' },
	    { name => 'dns' },
	    { name => 'firewall' },
	    { name => 'hardware' },
	    { name => 'hosts' },
	    { name => 'journal' },
	    { name => 'lxc' },
	    { name => 'migrateall' },
	    { name => 'netstat' },
	    { name => 'network' },
	    { name => 'qemu' },
	    { name => 'query-url-metadata' },
	    { name => 'replication' },
	    { name => 'report' },
	    { name => 'rrd' }, # fixme: remove?
	    { name => 'rrddata' },# fixme: remove?
	    { name => 'scan' },
	    { name => 'services' },
	    { name => 'spiceshell' },
	    { name => 'startall' },
	    { name => 'status' },
	    { name => 'stopall' },
	    { name => 'storage' },
	    { name => 'subscription' },
	    { name => 'suspendall' },
	    { name => 'syslog' },
	    { name => 'tasks' },
	    { name => 'termproxy' },
	    { name => 'time' },
	    { name => 'version' },
	    { name => 'vncshell' },
	    { name => 'vzdump' },
	    { name => 'wakeonlan' },
	];

	push @$result, { name => 'sdn' } if $have_sdn;

	return $result;
    }});

__PACKAGE__->register_method ({
    name => 'version',
    path => 'version',
    method => 'GET',
    proxyto => 'node',
    permissions => { user => 'all' },
    description => "API version details",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	},
    },
    returns => {
	type => "object",
	properties => {
	    version => {
		type => 'string',
		description => 'The current installed pve-manager package version',
	    },
	    release => {
		type => 'string',
		description => 'The current installed Proxmox VE Release',
	    },
	    repoid => {
		type => 'string',
		description => 'The short git commit hash ID from which this version was build',
	    },
	},
    },
    code => sub {
	my ($resp, $param) = @_;

	return PVE::pvecfg::version_info();
    }});

my sub get_current_kernel_info {
    my ($sysname, $nodename, $release, $version, $machine) = POSIX::uname();

    my $kernel_version_string = "$sysname $release $version"; # for legacy compat
    my $current_kernel = {
	sysname => $sysname,
	release => $release,
	version => $version,
	machine => $machine,
    };
    return ($current_kernel, $kernel_version_string);
}

my $boot_mode_info_cache;
my sub get_boot_mode_info {
    return $boot_mode_info_cache if defined($boot_mode_info_cache);

    my $is_efi_booted = -d "/sys/firmware/efi";

    $boot_mode_info_cache = {
	mode => $is_efi_booted ? 'efi' : 'legacy-bios',
    };

    my $efi_var = "/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c";

    if ($is_efi_booted && -e $efi_var) {
	my $efi_var_sec_boot_entry = eval { file_get_contents($efi_var) };
	if ($@) {
	    warn "Failed to read secure boot state: $@\n";
	} else {
	    my @secureboot = unpack("CCCCC", $efi_var_sec_boot_entry);
	    $boot_mode_info_cache->{secureboot} = $secureboot[4] == 1 ? 1 : 0;
	}
    }
    return $boot_mode_info_cache;
}

__PACKAGE__->register_method({
    name => 'status',
    path => 'status',
    method => 'GET',
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Audit' ]],
    },
    description => "Read node status",
    proxyto => 'node',
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	},
    },
    returns => {
	type => "object",
	additionalProperties => 1,
	properties => {
	    # TODO: document remaing ones
	    'boot-info' => {
		description => "Meta-information about the boot mode.",
		type => 'object',
		properties => {
		    mode => {
			description => 'Through which firmware the system got booted.',
			type => 'string',
			enum => [qw(efi legacy-bios)],
		    },
		    secureboot => {
			description => 'System is booted in secure mode, only applicable for the "efi" mode.',
			type => 'boolean',
			optional => 1,
		    },
		},
	    },
	    'current-kernel' => {
		description => "The uptime of the system in seconds.",
		type => 'object',
		properties => {
		    sysname => {
			description => 'OS kernel name (e.g., "Linux")',
			type => 'string',
		    },
		    release => {
			description => 'OS kernel release (e.g., "6.8.0")',
			type => 'string',
		    },
		    version => {
			description => 'OS kernel version with build info',
			type => 'string',
		    },
		    machine => {
			description => 'Hardware (architecture) type',
			type => 'string',
		    },
		},
	    },
	},
    },
    code => sub {
	my ($param) = @_;

	my $res = {
	    uptime => 0,
	    idle => 0,
	};

	my ($uptime, $idle) = PVE::ProcFSTools::read_proc_uptime();
	$res->{uptime} = $uptime;

	my ($avg1, $avg5, $avg15) = PVE::ProcFSTools::read_loadavg();
	$res->{loadavg} = [ $avg1, $avg5, $avg15];

	my ($current_kernel_info, $kversion_string) = get_current_kernel_info();
	$res->{kversion} = $kversion_string;
	$res->{'current-kernel'} = $current_kernel_info;

	$res->{'boot-info'} = get_boot_mode_info();

	$res->{cpuinfo} = PVE::ProcFSTools::read_cpuinfo();

	my $stat = PVE::ProcFSTools::read_proc_stat();
	$res->{cpu} = $stat->{cpu};
	$res->{wait} = $stat->{wait};

	my $meminfo = PVE::ProcFSTools::read_meminfo();
	$res->{memory} = {
	    free => $meminfo->{memfree},
	    total => $meminfo->{memtotal},
	    used => $meminfo->{memused},
	};

	$res->{ksm} = {
	    shared => $meminfo->{memshared},
	};

	$res->{swap} = {
	    free => $meminfo->{swapfree},
	    total => $meminfo->{swaptotal},
	    used => $meminfo->{swapused},
	};

	$res->{pveversion} = PVE::pvecfg::package() . "/" .
	    PVE::pvecfg::version_text();

	my $dinfo = df('/', 1);     # output is bytes

	$res->{rootfs} = {
	    total => $dinfo->{blocks},
	    avail => $dinfo->{bavail},
	    used => $dinfo->{used},
	    free => $dinfo->{blocks} - $dinfo->{used},
	};

	return $res;
    }});

__PACKAGE__->register_method({
    name => 'netstat',
    path => 'netstat',
    method => 'GET',
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Audit' ]],
    },
    description => "Read tap/vm network device interface counters",
    proxyto => 'node',
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	},
    },
    returns => {
	type => "array",
	items => {
	    type => "object",
	    properties => {},
	},
    },
    code => sub {
	my ($param) = @_;

	my $res = [ ];

	my $netdev = PVE::ProcFSTools::read_proc_net_dev();
	foreach my $dev (sort keys %$netdev) {
	    next if $dev !~ m/^(?:tap|veth)([1-9]\d*)i(\d+)$/;
	    my ($vmid, $netid) = ($1, $2);

	    push @$res, {
		vmid => $vmid,
		dev  => "net$netid",
		in   => $netdev->{$dev}->{transmit},
		out  => $netdev->{$dev}->{receive},
	    };
	}

	return $res;
    }});

__PACKAGE__->register_method({
    name => 'execute',
    path => 'execute',
    method => 'POST',
    description => "Execute multiple commands in order, root only.",
    proxyto => 'node',
    protected => 1, # avoid problems with proxy code
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    commands => {
		description => "JSON encoded array of commands.",
		type => "string",
		verbose_description => "JSON encoded array of commands, where each command is an object with the following properties:\n"
		 . PVE::RESTHandler::dump_properties($verify_command_item_desc->{items}->{properties}, 'full'),
		format => "pve-command-batch",
	    }
	},
    },
    returns => {
	type => 'array',
	items => {
	    type => "object",
	    properties => {},
	},
    },
    code => sub {
	my ($param) = @_;
	my $res = [];

	my $rpcenv = PVE::RPCEnvironment::get();
	my $user = $rpcenv->get_user();
	# just parse the json again, it should already be validated
	my $commands = eval { decode_json($param->{commands}); };

	foreach my $cmd (@$commands) {
	    eval {
		$cmd->{args} //= {};

		my $path = "nodes/$param->{node}/$cmd->{path}";

		my $uri_param = {};
		my ($handler, $info) = PVE::API2->find_handler($cmd->{method}, $path, $uri_param);
		if (!$handler || !$info) {
		    die "no handler for '$path'\n";
		}

		foreach my $p (keys %{$cmd->{args}}) {
		    raise_param_exc({ $p => "duplicate parameter" }) if defined($uri_param->{$p});
		    $uri_param->{$p} = $cmd->{args}->{$p};
		}

		# check access permissions
		$rpcenv->check_api2_permissions($info->{permissions}, $user, $uri_param);

		push @$res, {
		    status => HTTP_OK,
		    data => $handler->handle($info, $uri_param),
		};
	    };
	    if (my $err = $@) {
		my $resp = { status => HTTP_INTERNAL_SERVER_ERROR };
		if (ref($err) eq "PVE::Exception") {
		    $resp->{status} = $err->{code} if $err->{code};
		    $resp->{errors} = $err->{errors} if $err->{errors};
		    $resp->{message} = $err->{msg};
		} else {
		    $resp->{message} = $err;
		}
		push @$res, $resp;
	    }
	}

	return $res;
    }});


__PACKAGE__->register_method({
    name => 'node_cmd',
    path => 'status',
    method => 'POST',
    permissions => {
        check => ['perm', '/nodes/{node}', [ 'Sys.PowerMgmt' ]],
    },
    protected => 1,
    description => "Reboot, shutdown, or upgrade a node.",
    proxyto => 'node',
    parameters => {
        additionalProperties => 0,
        properties => {
            node => get_standard_option('pve-node'),
            command => {
                description => "Specify the command.",
                type => 'string',
                enum => [qw(reboot shutdown upgrade)],
            },
        },
    },
    returns => { type => "null" },
    code => sub {
        my ($param) = @_;

        if ($param->{command} eq 'reboot') {
            system ("(sleep 2;/sbin/reboot)&");
        } elsif ($param->{command} eq 'shutdown') {
            system ("(sleep 2;/sbin/poweroff)&");
        } elsif ($param->{command} eq 'upgrade') {
            system ("(sleep 2; /usr/bin/apt-get -y upgrade)&");
        }

        return;
    }});


__PACKAGE__->register_method({
    name => 'wakeonlan',
    path => 'wakeonlan',
    method => 'POST',
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.PowerMgmt' ]],
    },
    protected => 1,
    description => "Try to wake a node via 'wake on LAN' network packet.",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node', {
		description => 'target node for wake on LAN packet',
		completion => sub {
		    my $members = PVE::Cluster::get_members();
		    return [ grep { !$members->{$_}->{online} } keys %$members ];
		}
	    }),
	},
    },
    returns => {
	type => 'string',
	format => 'mac-addr',
	description => 'MAC address used to assemble the WoL magic packet.',
    },
    code => sub {
	my ($param) = @_;

	my $node = $param->{node};
	my $local_node = PVE::INotify::nodename();

	die "'$node' is local node, cannot wake my self!\n"
	    if $node eq 'localhost' || $node eq $local_node;

	PVE::Cluster::check_node_exists($node);

	my $config = PVE::NodeConfig::load_config($node);
	my $wol_config = PVE::NodeConfig::get_wakeonlan_config($config);
	my $mac_addr = $wol_config->{mac};
	if (!defined($mac_addr)) {
	    die "No wake on LAN MAC address defined for '$node'!\n";
	}

	my $local_config = PVE::NodeConfig::load_config($local_node);
	my $local_wol_config = PVE::NodeConfig::get_wakeonlan_config($local_config);
	my $broadcast_addr = $local_wol_config->{'broadcast-address'} // '255.255.255.255';

	$mac_addr =~ s/://g;
	my $packet = chr(0xff) x 6 . pack('H*', $mac_addr) x 16;

	my $addr = gethostbyname($broadcast_addr);
	my $port = getservbyname('discard', 'udp');
	my $to = Socket::pack_sockaddr_in($port, $addr);

	socket(my $sock, Socket::AF_INET, Socket::SOCK_DGRAM, Socket::IPPROTO_UDP)
	    || die "Unable to open socket: $!\n";
	setsockopt($sock, Socket::SOL_SOCKET, Socket::SO_BROADCAST, 1)
	    || die "Unable to set socket option: $!\n";

	if (defined(my $bind_iface = $local_wol_config->{'bind-interface'})) {
	    my $bind_iface_raw = pack('Z*', $bind_iface); # Null terminated interface name
	    setsockopt($sock, Socket::SOL_SOCKET, Socket::SO_BINDTODEVICE, $bind_iface_raw)
		|| die "Unable to bind socket to interface '$bind_iface': $!\n";
	}

	send($sock, $packet, 0, $to)
	    || die "Unable to send packet: $!\n";

	close($sock);

	return $wol_config->{mac};
    }});

__PACKAGE__->register_method({
    name => 'rrd',
    path => 'rrd',
    method => 'GET',
    protected => 1, # fixme: can we avoid that?
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Audit' ]],
    },
    description => "Read node RRD statistics (returns PNG)",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    timeframe => {
		description => "Specify the time frame you are interested in.",
		type => 'string',
		enum => [ 'hour', 'day', 'week', 'month', 'year' ],
	    },
	    ds => {
		description => "The list of datasources you want to display.",
		type => 'string', format => 'pve-configid-list',
	    },
	    cf => {
		description => "The RRD consolidation function",
		type => 'string',
		enum => [ 'AVERAGE', 'MAX' ],
		optional => 1,
	    },
	},
    },
    returns => {
	type => "object",
	properties => {
	    filename => { type => 'string' },
	},
    },
    code => sub {
	my ($param) = @_;

	return PVE::RRD::create_rrd_graph(
	    "pve2-node/$param->{node}", $param->{timeframe},
	    $param->{ds}, $param->{cf});

    }});

__PACKAGE__->register_method({
    name => 'rrddata',
    path => 'rrddata',
    method => 'GET',
    protected => 1, # fixme: can we avoid that?
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Audit' ]],
    },
    description => "Read node RRD statistics",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    timeframe => {
		description => "Specify the time frame you are interested in.",
		type => 'string',
		enum => [ 'hour', 'day', 'week', 'month', 'year' ],
	    },
	    cf => {
		description => "The RRD consolidation function",
		type => 'string',
		enum => [ 'AVERAGE', 'MAX' ],
		optional => 1,
	    },
	},
    },
    returns => {
	type => "array",
	items => {
	    type => "object",
	    properties => {},
	},
    },
    code => sub {
	my ($param) = @_;

	return PVE::RRD::create_rrd_data(
	    "pve2-node/$param->{node}", $param->{timeframe}, $param->{cf});
    }});

__PACKAGE__->register_method({
    name => 'syslog',
    path => 'syslog',
    method => 'GET',
    description => "Read system log",
    proxyto => 'node',
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Syslog' ]],
    },
    protected => 1,
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    start => {
		type => 'integer',
		minimum => 0,
		optional => 1,
	    },
	    limit => {
		type => 'integer',
		minimum => 0,
		optional => 1,
	    },
	    since => {
		type=> 'string',
		pattern => '^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}(:\d{2})?)?$',
		description => "Display all log since this date-time string.",
		optional => 1,
	    },
	    until => {
		type=> 'string',
		pattern => '^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}(:\d{2})?)?$',
		description => "Display all log until this date-time string.",
		optional => 1,
	    },
	    service => {
		description => "Service ID",
		type => 'string',
		maxLength => 128,
		optional => 1,
	    },
	},
    },
    returns => {
	type => 'array',
	items => {
	    type => "object",
	    properties => {
		n => {
		  description=>  "Line number",
		  type=> 'integer',
		},
		t => {
		  description=>  "Line text",
		  type => 'string',
		}
	    }
	}
    },
    code => sub {
	my ($param) = @_;

	my $rpcenv = PVE::RPCEnvironment::get();
	my $user = $rpcenv->get_user();
	my $node = $param->{node};
	my $service;

	if ($param->{service}) {
	    my $service_aliases = {
		'postfix' => 'postfix@-',
	    };

	    $service = $service_aliases->{$param->{service}} // $param->{service};
	}

	my ($count, $lines) = PVE::Tools::dump_journal($param->{start}, $param->{limit},
						       $param->{since}, $param->{until}, $service);

	$rpcenv->set_result_attrib('total', $count);

	return $lines;
    }});

__PACKAGE__->register_method({
    name => 'journal',
    path => 'journal',
    method => 'GET',
    description => "Read Journal",
    proxyto => 'node',
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Syslog' ]],
    },
    protected => 1,
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    since => {
		type=> 'integer',
		minimum => 0,
		description => "Display all log since this UNIX epoch. Conflicts with 'startcursor'.",
		optional => 1,
	    },
	    until => {
		type=> 'integer',
		minimum => 0,
		description => "Display all log until this UNIX epoch. Conflicts with 'endcursor'.",
		optional => 1,
	    },
	    lastentries => {
		description => "Limit to the last X lines. Conflicts with a range.",
		type => 'integer',
		minimum => 0,
		optional => 1,
	    },
	    startcursor => {
		description => "Start after the given Cursor. Conflicts with 'since'",
		type => 'string',
		optional => 1,
	    },
	    endcursor => {
		description => "End before the given Cursor. Conflicts with 'until'",
		type => 'string',
		optional => 1,
	    },
	},
    },
    returns => {
	type => 'array',
	items => {
	    type => "string",
	}
    },
    code => sub {
	my ($param) = @_;

	my $rpcenv = PVE::RPCEnvironment::get();
	my $user = $rpcenv->get_user();

	my $cmd = ["/usr/bin/mini-journalreader", "-j"];
	push @$cmd, '-n', $param->{lastentries} if $param->{lastentries};
	push @$cmd, '-b', $param->{since} if $param->{since};
	push @$cmd, '-e', $param->{until} if $param->{until};
	push @$cmd, '-f', PVE::Tools::shellquote($param->{startcursor}) if $param->{startcursor};
	push @$cmd, '-t', PVE::Tools::shellquote($param->{endcursor}) if $param->{endcursor};
	push @$cmd, ' | gzip ';

	open(my $fh, "-|", join(' ', @$cmd))
	    or die "could not start mini-journalreader";

	return {
	    download => {
		fh => $fh,
		stream => 1,
		'content-type' => 'application/json',
		'content-encoding' => 'gzip',
	    },
	},
    }});

my $sslcert;

my $shell_cmd_map = {
    'login' => {
	cmd => [ '/bin/login', '-f', 'root' ],
    },
    'upgrade' => {
	cmd => [ '/usr/bin/pveupgrade', '--shell' ],
    },
    'ceph_install' => {
	cmd => [ '/usr/bin/pveceph', 'install' ],
	allow_args => 1,
    },
};

sub get_shell_command  {
    my ($user, $shellcmd, $args) = @_;

    my $cmd;
    if ($user eq 'root@pam') {
	if (defined($shellcmd) && exists($shell_cmd_map->{$shellcmd})) {
	    my $def = $shell_cmd_map->{$shellcmd};
	    $cmd = [ @{$def->{cmd}} ]; # clone
	    if (defined($args) && $def->{allow_args}) {
		push @$cmd, split("\0", $args);
	    }
	} else {
	    $cmd = [ '/bin/login', '-f', 'root' ];
	}
    } else {
	# non-root must always login for now, we do not have a superuser role!
	$cmd = [ '/bin/login' ];
    }
    return $cmd;
}

my $get_vnc_connection_info = sub {
    my $node = shift;

    my $remote_cmd = [];

    my ($remip, $family);
    if ($node ne 'localhost' && $node ne PVE::INotify::nodename()) {
	($remip, $family) = PVE::Cluster::remote_node_ip($node);
	$remote_cmd = PVE::SSHInfo::ssh_info_to_command({ ip => $remip, name => $node }, ('-t'));
	push @$remote_cmd, '--';
    } else {
	$family = PVE::Tools::get_host_address_family($node);
    }
    my $port = PVE::Tools::next_vnc_port($family);

    return ($port, $remote_cmd);
};

__PACKAGE__->register_method ({
    name => 'vncshell',
    path => 'vncshell',
    method => 'POST',
    protected => 1,
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Console' ]],
    },
    description => "Creates a VNC Shell proxy.",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    cmd => {
		type => 'string',
		description => "Run specific command or default to login (requires 'root\@pam')",
		enum => [keys %$shell_cmd_map],
		optional => 1,
		default => 'login',
	    },
	    'cmd-opts' => {
		type => 'string',
		description => "Add parameters to a command. Encoded as null terminated strings.",
		requires => 'cmd',
		optional => 1,
		default => '',
	    },
	    websocket => {
		optional => 1,
		type => 'boolean',
		description => "use websocket instead of standard vnc.",
	    },
	    width => {
		optional => 1,
		description => "sets the width of the console in pixels.",
		type => 'integer',
		minimum => 16,
		maximum => 4096,
	    },
	    height => {
		optional => 1,
		description => "sets the height of the console in pixels.",
		type => 'integer',
		minimum => 16,
		maximum => 2160,
	    },
	},
    },
    returns => {
	additionalProperties => 0,
	properties => {
	    user => { type => 'string' },
	    ticket => { type => 'string' },
	    cert => { type => 'string' },
	    port => { type => 'integer' },
	    upid => { type => 'string' },
	},
    },
    code => sub {
	my ($param) = @_;

	my $rpcenv = PVE::RPCEnvironment::get();
	my ($user, undef, $realm) = PVE::AccessControl::verify_username($rpcenv->get_user());


	if (defined($param->{cmd}) && $param->{cmd} ne 'login' && $user ne 'root@pam') {
	    raise_perm_exc('user != root@pam');
	}

	my $node = $param->{node};

	my $authpath = "/nodes/$node";
	my $ticket = PVE::AccessControl::assemble_vnc_ticket($user, $authpath);

	$sslcert = PVE::Tools::file_get_contents("/etc/pve/pve-root-ca.pem", 8192)
	    if !$sslcert;

	my ($port, $remcmd) = $get_vnc_connection_info->($node);

	my $shcmd = get_shell_command($user, $param->{cmd}, $param->{'cmd-opts'});

	my $timeout = 10;

	my $cmd = ['/usr/bin/vncterm',
	    '-rfbport', $port,
	    '-timeout', $timeout,
	    '-authpath', $authpath,
	    '-perm', 'Sys.Console',
	];

	push @$cmd, '-width', $param->{width} if $param->{width};
	push @$cmd, '-height', $param->{height} if $param->{height};

	if ($param->{websocket}) {
	    $ENV{PVE_VNC_TICKET} = $ticket; # pass ticket to vncterm
	    push @$cmd, '-notls', '-listen', 'localhost';
	}

	push @$cmd, '-c', @$remcmd, @$shcmd;

	my $realcmd = sub {
	    my $upid = shift;

	    syslog ('info', "starting vnc proxy $upid\n");

	    my $cmdstr = join (' ', @$cmd);
	    syslog ('info', "launch command: $cmdstr");

	    eval {
		foreach my $k (keys %ENV) {
		    next if $k eq 'PVE_VNC_TICKET';
		    next if $k eq 'PATH' || $k eq 'TERM' || $k eq 'USER' || $k eq 'HOME' || $k eq 'LANG' || $k eq 'LANGUAGE';
		    delete $ENV{$k};
		}
		$ENV{PWD} = '/';

		PVE::Tools::run_command($cmd, errmsg => "vncterm failed", keeplocale => 1);
	    };
	    if (my $err = $@) {
		syslog ('err', $err);
	    }

	    return;
	};

	my $upid = $rpcenv->fork_worker('vncshell', "", $user, $realcmd);

	PVE::Tools::wait_for_vnc_port($port);

	return {
	    user => $user,
	    ticket => $ticket,
	    port => $port,
	    upid => $upid,
	    cert => $sslcert,
	};
    }});

__PACKAGE__->register_method ({
    name => 'termproxy',
    path => 'termproxy',
    method => 'POST',
    protected => 1,
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Console' ]],
    },
    description => "Creates a VNC Shell proxy.",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    cmd => {
		type => 'string',
		description => "Run specific command or default to login (requires 'root\@pam')",
		enum => [keys %$shell_cmd_map],
		optional => 1,
		default => 'login',
	    },
	    'cmd-opts' => {
		type => 'string',
		description => "Add parameters to a command. Encoded as null terminated strings.",
		requires => 'cmd',
		optional => 1,
		default => '',
	    },
	},
    },
    returns => {
	additionalProperties => 0,
	properties => {
	    user => { type => 'string' },
	    ticket => { type => 'string' },
	    port => { type => 'integer' },
	    upid => { type => 'string' },
	},
    },
    code => sub {
	my ($param) = @_;

	my $rpcenv = PVE::RPCEnvironment::get();
	my ($user, undef, $realm) = PVE::AccessControl::verify_username($rpcenv->get_user());

	my $node = $param->{node};
	my $authpath = "/nodes/$node";
	my $ticket = PVE::AccessControl::assemble_vnc_ticket($user, $authpath);

	my ($port, $remcmd) = $get_vnc_connection_info->($node);

	my $shcmd = get_shell_command($user, $param->{cmd}, $param->{'cmd-opts'});

	my $realcmd = sub {
	    my $upid = shift;

	    syslog ('info', "starting termproxy $upid\n");

	    my $cmd = [
		'/usr/bin/termproxy',
		$port,
		'--path', $authpath,
		'--perm', 'Sys.Console',
		'--'
	    ];
	    push  @$cmd, @$remcmd, @$shcmd;

	    PVE::Tools::run_command($cmd);
	};
	my $upid = $rpcenv->fork_worker('vncshell', "", $user, $realcmd);

	PVE::Tools::wait_for_vnc_port($port);

	return {
	    user => $user,
	    ticket => $ticket,
	    port => $port,
	    upid => $upid,
	};
    }});

__PACKAGE__->register_method({
    name => 'vncwebsocket',
    path => 'vncwebsocket',
    method => 'GET',
    permissions => {
	description => "You also need to pass a valid ticket (vncticket).",
	check => ['perm', '/nodes/{node}', [ 'Sys.Console' ]],
    },
    description => "Opens a websocket for VNC traffic.",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    vncticket => {
		description => "Ticket from previous call to vncproxy.",
		type => 'string',
		maxLength => 512,
	    },
	    port => {
		description => "Port number returned by previous vncproxy call.",
		type => 'integer',
		minimum => 5900,
		maximum => 5999,
	    },
	},
    },
    returns => {
	type => "object",
	properties => {
	    port => { type => 'string' },
	},
    },
    code => sub {
	my ($param) = @_;

	my $rpcenv = PVE::RPCEnvironment::get();

	my ($user, undef, $realm) = PVE::AccessControl::verify_username($rpcenv->get_user());

	my $authpath = "/nodes/$param->{node}";

	PVE::AccessControl::verify_vnc_ticket($param->{vncticket}, $user, $authpath);

	my $port = $param->{port};

	return { port => $port };
    }});

__PACKAGE__->register_method ({
    name => 'spiceshell',
    path => 'spiceshell',
    method => 'POST',
    protected => 1,
    proxyto => 'node',
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Console' ]],
    },
    description => "Creates a SPICE shell.",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    proxy => get_standard_option('spice-proxy', { optional => 1 }),
	    cmd => {
		type => 'string',
		description => "Run specific command or default to login (requires 'root\@pam')",
		enum => [keys %$shell_cmd_map],
		optional => 1,
		default => 'login',
	    },
	    'cmd-opts' => {
		type => 'string',
		description => "Add parameters to a command. Encoded as null terminated strings.",
		requires => 'cmd',
		optional => 1,
		default => '',
	    },
	},
    },
    returns => get_standard_option('remote-viewer-config'),
    code => sub {
	my ($param) = @_;

	my $rpcenv = PVE::RPCEnvironment::get();
	my $authuser = $rpcenv->get_user();

	my ($user, undef, $realm) = PVE::AccessControl::verify_username($authuser);


	if (defined($param->{cmd}) && $param->{cmd} ne 'login' && $user ne 'root@pam') {
	    raise_perm_exc('user != root@pam');
	}

	my $node = $param->{node};
	my $proxy = $param->{proxy};

	my $authpath = "/nodes/$node";
	my $permissions = 'Sys.Console';

	my $shcmd = get_shell_command($user, $param->{cmd}, $param->{'cmd-opts'});

	my $title = "Shell on '$node'";

	return PVE::API2Tools::run_spiceterm($authpath, $permissions, 0, $node, $proxy, $title, $shcmd);
    }});

__PACKAGE__->register_method({
    name => 'dns',
    path => 'dns',
    method => 'GET',
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Audit' ]],
    },
    description => "Read DNS settings.",
    proxyto => 'node',
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	},
    },
    returns => {
	type => "object",
	additionalProperties => 0,
	properties => {
	    search => {
		description => "Search domain for host-name lookup.",
		type => 'string',
		optional => 1,
	    },
	    dns1 => {
		description => 'First name server IP address.',
		type => 'string',
		optional => 1,
	    },
	    dns2 => {
		description => 'Second name server IP address.',
		type => 'string',
		optional => 1,
	    },
	    dns3 => {
		description => 'Third name server IP address.',
		type => 'string',
		optional => 1,
	    },
	},
    },
    code => sub {
	my ($param) = @_;

	my $res = PVE::INotify::read_file('resolvconf');

	return $res;
    }});

__PACKAGE__->register_method({
    name => 'update_dns',
    path => 'dns',
    method => 'PUT',
    description => "Write DNS settings.",
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Modify' ]],
    },
    proxyto => 'node',
    protected => 1,
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    search => {
		description => "Search domain for host-name lookup.",
		type => 'string',
	    },
	    dns1 => {
		description => 'First name server IP address.',
		type => 'string', format => 'ip',
		optional => 1,
	    },
	    dns2 => {
		description => 'Second name server IP address.',
		type => 'string', format => 'ip',
		optional => 1,
	    },
	    dns3 => {
		description => 'Third name server IP address.',
		type => 'string', format => 'ip',
		optional => 1,
	    },
	},
    },
    returns => { type => "null" },
    code => sub {
	my ($param) = @_;

	PVE::INotify::update_file('resolvconf', $param);

	return;
    }});

__PACKAGE__->register_method({
    name => 'time',
    path => 'time',
    method => 'GET',
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Audit' ]],
   },
    description => "Read server time and time zone settings.",
    proxyto => 'node',
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	},
    },
    returns => {
	type => "object",
	additionalProperties => 0,
	properties => {
	    timezone => {
		description => "Time zone",
		type => 'string',
	    },
	    time => {
		description => "Seconds since 1970-01-01 00:00:00 UTC.",
		type => 'integer',
		minimum => 1297163644,
		renderer => 'timestamp',
	    },
	    localtime => {
		description => "Seconds since 1970-01-01 00:00:00 (local time)",
		type => 'integer',
		minimum => 1297163644,
		renderer => 'timestamp_gmt',
	    },
	},
    },
    code => sub {
	my ($param) = @_;

	my $ctime = time();
	my $ltime = timegm_nocheck(localtime($ctime));
	my $res = {
	    timezone => PVE::INotify::read_file('timezone'),
	    time => $ctime,
	    localtime => $ltime,
	};

	return $res;
    }});

__PACKAGE__->register_method({
    name => 'set_timezone',
    path => 'time',
    method => 'PUT',
    description => "Set time zone.",
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Modify' ]],
    },
    proxyto => 'node',
    protected => 1,
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    timezone => {
		description => "Time zone. The file '/usr/share/zoneinfo/zone.tab' contains the list of valid names.",
		type => 'string',
	    },
	},
    },
    returns => { type => "null" },
    code => sub {
	my ($param) = @_;

	PVE::INotify::write_file('timezone', $param->{timezone});

	return;
    }});

__PACKAGE__->register_method({
    name => 'aplinfo',
    path => 'aplinfo',
    method => 'GET',
    permissions => {
	user => 'all',
    },
    description => "Get list of appliances.",
    proxyto => 'node',
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	},
    },
    returns => {
	type => 'array',
	items => {
	    type => "object",
	    properties => {},
	},
    },
    code => sub {
	my ($param) = @_;

	my $list = PVE::APLInfo::load_data();

	my $res = [];
	for my $appliance (values %{$list->{all}}) {
	    next if $appliance->{'package'} eq 'pve-web-news';
	    push @$res, $appliance;
	}

	return $res;
    }});

__PACKAGE__->register_method({
    name => 'apl_download',
    path => 'aplinfo',
    method => 'POST',
    permissions => {
	check => ['perm', '/storage/{storage}', ['Datastore.AllocateTemplate']],
    },
    description => "Download appliance templates.",
    proxyto => 'node',
    protected => 1,
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    storage => get_standard_option('pve-storage-id', {
		description => "The storage where the template will be stored",
		completion => \&PVE::Storage::complete_storage_enabled,
	    }),
	    template => {
		type => 'string',
		description => "The template which will downloaded",
		maxLength => 255,
		completion => \&complete_templet_repo,
	    },
	},
    },
    returns => { type => "string" },
    code => sub {
	my ($param) = @_;

	my $rpcenv = PVE::RPCEnvironment::get();
	my $user = $rpcenv->get_user();

	my $node = $param->{node};
	my $template = $param->{template};

	my $list = PVE::APLInfo::load_data();
	my $appliance = $list->{all}->{$template};
	raise_param_exc({ template => "no such template"}) if !$appliance;

	my $cfg = PVE::Storage::config();
	my $scfg = PVE::Storage::storage_check_enabled($cfg, $param->{storage}, $node);

	die "unknown template type '$appliance->{type}'\n"
	    if !($appliance->{type} eq 'openvz' || $appliance->{type} eq 'lxc');

	die "storage '$param->{storage}' does not support templates\n"
	    if !$scfg->{content}->{vztmpl};

	my $tmpldir = PVE::Storage::get_vztmpl_dir($cfg, $param->{storage});

	my $worker = sub {
	    my $dccfg = PVE::Cluster::cfs_read_file('datacenter.cfg');

	    PVE::Tools::download_file_from_url("$tmpldir/$template", $appliance->{location}, {
		hash_required => 1,
		sha512sum => $appliance->{sha512sum},
		md5sum => $appliance->{md5sum},
		http_proxy => $dccfg->{http_proxy},
	    });
	};

	my $upid = $rpcenv->fork_worker('download', $template, $user, $worker);

	return $upid;
    }});

__PACKAGE__->register_method({
    name => 'query_url_metadata',
    path => 'query-url-metadata',
    method => 'GET',
    description => "Query metadata of an URL: file size, file name and mime type.",
    proxyto => 'node',
    permissions => {
	check => ['or',
	    ['perm', '/', [ 'Sys.Audit', 'Sys.Modify' ]],
	    ['perm', '/nodes/{node}', [ 'Sys.AccessNetwork' ]],
	],
    },
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    url => {
		description => "The URL to query the metadata from.",
		type => 'string',
		pattern => 'https?://.*',
	    },
	    'verify-certificates' => {
		description => "If false, no SSL/TLS certificates will be verified.",
		type => 'boolean',
		optional => 1,
		default => 1,
	    },
	},
    },
    returns => {
	type => "object",
	properties => {
	    filename => {
		type => 'string',
		optional => 1,
	    },
	    size => {
		type => 'integer',
		renderer => 'bytes',
		optional => 1,
	    },
	    mimetype => {
		type => 'string',
		optional => 1,
	    },
	},
    },
    code => sub {
	my ($param) = @_;

	my $url = $param->{url};

	my $ua = LWP::UserAgent->new();
	$ua->agent("Proxmox VE");

	my $dccfg = PVE::Cluster::cfs_read_file('datacenter.cfg');
	if ($dccfg->{http_proxy}) {
	    $ua->proxy('http', $dccfg->{http_proxy});
	}

	my $verify = $param->{'verify-certificates'} // 1;
	if (!$verify) {
	    $ua->ssl_opts(
		verify_hostname => 0,
		SSL_verify_mode => IO::Socket::SSL::SSL_VERIFY_NONE,
	    );
	}

	my $req = HTTP::Request->new(HEAD => $url);
	my $res = $ua->request($req);

	die "invalid server response: '" . $res->status_line() . "'\n" if ($res->code() != 200);

	my $size = $res->header("Content-Length");
	my $disposition = $res->header("Content-Disposition");
	my $type = $res->header("Content-Type");

	my $filename;

	if ($disposition && ($disposition =~ m/filename="([^"]*)"/ || $disposition =~ m/filename=([^;]*)/)) {
	    $filename = $1;
	} elsif ($url =~ m!^[^?]+/([^?/]*)(?:\?.*)?$!) {
	    $filename = $1;
	}

	# Content-Type: text/html; charset=utf-8
	if ($type && $type =~ m/^([^;]+);/) {
	    $type = $1;
	}

	my $ret = {};
	$ret->{filename} = $filename if $filename;
	$ret->{size} = $size + 0 if $size;
	$ret->{mimetype} = $type if $type;

	return $ret;
    }});

__PACKAGE__->register_method({
    name => 'report',
    path => 'report',
    method => 'GET',
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Audit' ]],
    },
    protected => 1,
    description => "Gather various systems information about a node",
    proxyto => 'node',
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	},
    },
    returns => {
	type => 'string',
    },
    code => sub {
	return PVE::Report::generate();
    }});

# returns a list of VMIDs, those can be filtered by
# * current parent node
# * vmid whitelist
# * guest is a template (default: skip)
# * guest is HA manged (default: skip)
my $get_filtered_vmlist = sub {
    my ($nodename, $vmfilter, $templates, $ha_managed) = @_;

    my $vmlist = PVE::Cluster::get_vmlist();

    my $vms_allowed;
    if (defined($vmfilter)) {
	$vms_allowed = { map { $_ => 1 } PVE::Tools::split_list($vmfilter) };
    }

    my $res = {};
    foreach my $vmid (keys %{$vmlist->{ids}}) {
	next if defined($vms_allowed) && !$vms_allowed->{$vmid};

	my $d = $vmlist->{ids}->{$vmid};
	next if $nodename && $d->{node} ne $nodename;

	eval {
	    my $class;
	    if ($d->{type} eq 'lxc') {
		$class = 'PVE::LXC::Config';
	    } elsif ($d->{type} eq 'qemu') {
		$class = 'PVE::QemuConfig';
	    } else {
		die "unknown virtual guest type '$d->{type}'\n";
	    }

	    my $conf = $class->load_config($vmid);
	    return if !$templates && $class->is_template($conf);
	    return if !$ha_managed && PVE::HA::Config::vm_is_ha_managed($vmid);

	    $res->{$vmid}->{conf} = $conf;
	    $res->{$vmid}->{type} = $d->{type};
	    $res->{$vmid}->{class} = $class;
	};
	warn $@ if $@;
    }

    return $res;
};

# return all VMs which should get started/stopped on power up/down
my $get_start_stop_list = sub {
    my ($nodename, $autostart, $vmfilter) = @_;

    # do not skip HA vms on force or if a specific VMID set is wanted
    my $include_ha_managed = defined($vmfilter) ? 1 : 0;

    my $vmlist = $get_filtered_vmlist->($nodename, $vmfilter, undef, $include_ha_managed);

    my $resList = {};
    foreach my $vmid (keys %$vmlist) {
	my $conf = $vmlist->{$vmid}->{conf};
	next if $autostart && !$conf->{onboot};

	my $startup = $conf->{startup} ? PVE::JSONSchema::pve_parse_startup_order($conf->{startup}) : {};
	my $order = $startup->{order} = $startup->{order} // LONG_MAX;

	$resList->{$order}->{$vmid} = $startup;
	$resList->{$order}->{$vmid}->{type} = $vmlist->{$vmid}->{type};
    }

    return $resList;
};

my $remove_locks_on_startup = sub {
    my ($nodename) = @_;

    my $vmlist = &$get_filtered_vmlist($nodename, undef, undef, 1);

    foreach my $vmid (keys %$vmlist) {
	my $conf = $vmlist->{$vmid}->{conf};
	my $class = $vmlist->{$vmid}->{class};

	eval {
	    if ($class->has_lock($conf, 'backup')) {
		$class->remove_lock($vmid, 'backup');
		my $msg =  "removed left over backup lock from '$vmid'!";
		warn "$msg\n"; # prints to task log
		syslog('warning', $msg);
	    }
	}; warn $@ if $@;
    }
};

__PACKAGE__->register_method ({
    name => 'startall',
    path => 'startall',
    method => 'POST',
    protected => 1,
    permissions => {
	description => "The 'VM.PowerMgmt' permission is required on '/' or on '/vms/<ID>' for "
	    ."each ID passed via the 'vms' parameter.",
	user => 'all',
    },
    proxyto => 'node',
    description => "Start all VMs and containers located on this node (by default only those with onboot=1).",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    force => {
		optional => 1,
		type => 'boolean',
		default => 'off',
		description => "Issue start command even if virtual guest have 'onboot' not set or set to off.",
	    },
	    vms => {
		description => "Only consider guests from this comma separated list of VMIDs.",
		type => 'string',  format => 'pve-vmid-list',
		optional => 1,
	    },
	},
    },
    returns => {
	type => 'string',
    },
    code => sub {
	my ($param) = @_;

	my $rpcenv = PVE::RPCEnvironment::get();
	my $authuser = $rpcenv->get_user();

	if (!$rpcenv->check($authuser, "/", [ 'VM.PowerMgmt' ], 1)) {
	    my @vms = PVE::Tools::split_list($param->{vms});
	    if (scalar(@vms) > 0) {
		$rpcenv->check($authuser, "/vms/$_", [ 'VM.PowerMgmt' ]) for @vms;
	    } else {
		raise_perm_exc("/, VM.PowerMgmt");
	    }
	}

	my $nodename = $param->{node};
	$nodename = PVE::INotify::nodename() if $nodename eq 'localhost';

	my $force = $param->{force};

	my $code = sub {
	    $rpcenv->{type} = 'priv'; # to start tasks in background

	    if (!PVE::Cluster::check_cfs_quorum(1)) {
		print "waiting for quorum ...\n";
		do {
		    sleep(1);
		} while (!PVE::Cluster::check_cfs_quorum(1));
		print "got quorum\n";
	    }

	    eval { # remove backup locks, but avoid running into a scheduled backup job
		PVE::Tools::lock_file('/var/run/vzdump.lock', 10, $remove_locks_on_startup, $nodename);
	    };
	    warn $@ if $@;

	    my $autostart = $force ? undef : 1;
	    my $startList = $get_start_stop_list->($nodename, $autostart, $param->{vms});

	    # Note: use numeric sorting with <=>
	    for my $order (sort {$a <=> $b} keys %$startList) {
		my $vmlist = $startList->{$order};

		for my $vmid (sort {$a <=> $b} keys %$vmlist) {
		    my $d = $vmlist->{$vmid};

		    PVE::Cluster::check_cfs_quorum(); # abort when we loose quorum

		    eval {
			my $default_delay = 0;
			my $upid;

			if ($d->{type} eq 'lxc') {
			    return if PVE::LXC::check_running($vmid);
			    print STDERR "Starting CT $vmid\n";
			    $upid = PVE::API2::LXC::Status->vm_start({node => $nodename, vmid => $vmid });
			} elsif ($d->{type} eq 'qemu') {
			    $default_delay = 3; # to reduce load
			    return if PVE::QemuServer::check_running($vmid, 1);
			    print STDERR "Starting VM $vmid\n";
			    $upid = PVE::API2::Qemu->vm_start({node => $nodename, vmid => $vmid });
			} else {
			    die "unknown VM type '$d->{type}'\n";
			}

			my $task = PVE::Tools::upid_decode($upid);
			while (PVE::ProcFSTools::check_process_running($task->{pid})) {
			    sleep(1);
			}

			my $status = PVE::Tools::upid_read_status($upid);
			if (!PVE::Tools::upid_status_is_error($status)) {
			    # use default delay to reduce load
			    my $delay = defined($d->{up}) ? int($d->{up}) : $default_delay;
			    if ($delay > 0) {
				print STDERR "Waiting for $delay seconds (startup delay)\n" if $d->{up};
				for (my $i = 0; $i < $delay; $i++) {
				    sleep(1);
				}
			    }
			} else {
			    my $rendered_type = $d->{type} eq 'lxc' ? 'CT' : 'VM';
			    print STDERR "Starting $rendered_type $vmid failed: $status\n";
			}
		    };
		    warn $@ if $@;
		}
	    }
	    return;
	};

	return $rpcenv->fork_worker('startall', undef, $authuser, $code);
    }});

my $create_stop_worker = sub {
    my ($nodename, $type, $vmid, $timeout, $force_stop) = @_;

    if ($type eq 'lxc') {
	return if !PVE::LXC::check_running($vmid);
	print STDERR "Stopping CT $vmid (timeout = $timeout seconds)\n";
	return PVE::API2::LXC::Status->vm_shutdown(
	    { node => $nodename, vmid => $vmid, timeout => $timeout, forceStop => $force_stop }
	);
    } elsif ($type eq 'qemu') {
	return if !PVE::QemuServer::check_running($vmid, 1);
	print STDERR "Stopping VM $vmid (timeout = $timeout seconds)\n";
	return PVE::API2::Qemu->vm_shutdown(
	    { node => $nodename, vmid => $vmid, timeout => $timeout, forceStop => $force_stop }
	);
    } else {
	die "unknown VM type '$type'\n";
    }
};

__PACKAGE__->register_method ({
    name => 'stopall',
    path => 'stopall',
    method => 'POST',
    protected => 1,
    permissions => {
	description => "The 'VM.PowerMgmt' permission is required on '/' or on '/vms/<ID>' for "
	    ."each ID passed via the 'vms' parameter.",
	user => 'all',
    },
    proxyto => 'node',
    description => "Stop all VMs and Containers.",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    vms => {
		description => "Only consider Guests with these IDs.",
		type => 'string',  format => 'pve-vmid-list',
		optional => 1,
	    },
	    'force-stop' => {
		description => 'Force a hard-stop after the timeout.',
		type => 'boolean',
		default => 1,
		optional => 1,
	    },
	    'timeout' => {
		description => 'Timeout for each guest shutdown task. Depending on `force-stop`,'
		    .' the shutdown gets then simply aborted or a hard-stop is forced.',
		type => 'integer',
		optional => 1,
		default => 180,
		minimum => 0,
		maximum => 2 * 3600, # mostly arbitrary, but we do not want to high timeouts
	    },
	},
    },
    returns => {
	type => 'string',
    },
    code => sub {
	my ($param) = @_;

	my $rpcenv = PVE::RPCEnvironment::get();
	my $authuser = $rpcenv->get_user();

	if (!$rpcenv->check($authuser, "/", [ 'VM.PowerMgmt' ], 1)) {
	    my @vms = PVE::Tools::split_list($param->{vms});
	    if (scalar(@vms) > 0) {
		$rpcenv->check($authuser, "/vms/$_", [ 'VM.PowerMgmt' ]) for @vms;
	    } else {
		raise_perm_exc("/, VM.PowerMgmt");
	    }
	}

	my $nodename = $param->{node};
	$nodename = PVE::INotify::nodename() if $nodename eq 'localhost';

	my $code = sub {

	    $rpcenv->{type} = 'priv'; # to start tasks in background

	    my $stopList = $get_start_stop_list->($nodename, undef, $param->{vms});

	    my $cpuinfo = PVE::ProcFSTools::read_cpuinfo();
	    my $datacenterconfig = cfs_read_file('datacenter.cfg');
	    # if not set by user spawn max cpu count number of workers
	    my $maxWorkers =  $datacenterconfig->{max_workers} || $cpuinfo->{cpus};

	    for my $order (sort {$b <=> $a} keys %$stopList) {
		my $vmlist = $stopList->{$order};
		my $workers = {};

		my $finish_worker = sub {
		    my $pid = shift;
		    my $worker = delete $workers->{$pid} || return;

		    syslog('info', "end task $worker->{upid}");
		};

		for my $vmid (sort {$b <=> $a} keys %$vmlist) {
		    my $d = $vmlist->{$vmid};
		    my $timeout = int($d->{down} // $param->{timeout} // 180);
		    my $upid = eval {
			$create_stop_worker->(
			    $nodename, $d->{type}, $vmid, $timeout, $param->{'force-stop'} // 1)
		    };
		    warn $@ if $@;
		    next if !$upid;

		    my $task = PVE::Tools::upid_decode($upid, 1);
		    next if !$task;

		    my $pid = $task->{pid};

		    $workers->{$pid} = { type => $d->{type}, upid => $upid, vmid => $vmid };
		    while (scalar(keys %$workers) >= $maxWorkers) {
			foreach my $p (keys %$workers) {
			    if (!PVE::ProcFSTools::check_process_running($p)) {
				$finish_worker->($p);
			    }
			}
			sleep(1);
		    }
		}
		while (scalar(keys %$workers)) {
		    for my $p (keys %$workers) {
			if (!PVE::ProcFSTools::check_process_running($p)) {
			    $finish_worker->($p);
			}
		    }
		    sleep(1);
		}
	    }

	    syslog('info', "all VMs and CTs stopped");

	    return;
	};

	return $rpcenv->fork_worker('stopall', undef, $authuser, $code);
    }});

my $create_suspend_worker = sub {
    my ($nodename, $vmid) = @_;
    if (!PVE::QemuServer::check_running($vmid, 1)) {
	print "VM $vmid not running, skipping suspension\n";
	return;
    }
    print STDERR "Suspending VM $vmid\n";
    return PVE::API2::Qemu->vm_suspend(
	{ node => $nodename, vmid => $vmid, todisk => 1 }
    );
};

__PACKAGE__->register_method ({
    name => 'suspendall',
    path => 'suspendall',
    method => 'POST',
    protected => 1,
    permissions => {
	description => "The 'VM.PowerMgmt' permission is required on '/' or on '/vms/<ID>' for each"
	    ." ID passed via the 'vms' parameter. Additionally, you need 'VM.Config.Disk' on the"
	    ." '/vms/{vmid}' path and 'Datastore.AllocateSpace' for the configured state-storage(s)",
	user => 'all',
    },
    proxyto => 'node',
    description => "Suspend all VMs.",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    vms => {
		description => "Only consider Guests with these IDs.",
		type => 'string',  format => 'pve-vmid-list',
		optional => 1,
	    },
	},
    },
    returns => {
	type => 'string',
    },
    code => sub {
	my ($param) = @_;

	my $rpcenv = PVE::RPCEnvironment::get();
	my $authuser = $rpcenv->get_user();

	# we cannot really check access to the state-storage here, that's happening per worker.
	if (!$rpcenv->check($authuser, "/", [ 'VM.PowerMgmt', 'VM.Config.Disk' ], 1)) {
	    my @vms = PVE::Tools::split_list($param->{vms});
	    if (scalar(@vms) > 0) {
		$rpcenv->check($authuser, "/vms/$_", [ 'VM.PowerMgmt' ]) for @vms;
	    } else {
		raise_perm_exc("/, VM.PowerMgmt && VM.Config.Disk");
	    }
	}

	my $nodename = $param->{node};
	$nodename = PVE::INotify::nodename() if $nodename eq 'localhost';

	my $code = sub {

	    $rpcenv->{type} = 'priv'; # to start tasks in background

	    my $toSuspendList = $get_start_stop_list->($nodename, undef, $param->{vms});

	    my $cpuinfo = PVE::ProcFSTools::read_cpuinfo();
	    my $datacenterconfig = cfs_read_file('datacenter.cfg');
	    # if not set by user spawn max cpu count number of workers
	    my $maxWorkers =  $datacenterconfig->{max_workers} || $cpuinfo->{cpus};

	    for my $order (sort {$b <=> $a} keys %$toSuspendList) {
		my $vmlist = $toSuspendList->{$order};
		my $workers = {};

		my $finish_worker = sub {
		    my $pid = shift;
		    my $worker = delete $workers->{$pid} || return;

		    syslog('info', "end task $worker->{upid}");
		};

		for my $vmid (sort {$b <=> $a} keys %$vmlist) {
		    my $d = $vmlist->{$vmid};
		    if ($d->{type} ne 'qemu') {
			log_warn("skipping $vmid, only VMs can be suspended");
			next;
		    }
		    my $upid = eval {
			$create_suspend_worker->($nodename, $vmid)
		    };
		    warn $@ if $@;
		    next if !$upid;

		    my $task = PVE::Tools::upid_decode($upid, 1);
		    next if !$task;

		    my $pid = $task->{pid};
		    $workers->{$pid} = { type => $d->{type}, upid => $upid, vmid => $vmid };

		    while (scalar(keys %$workers) >= $maxWorkers) {
			for my $p (keys %$workers) {
			    if (!PVE::ProcFSTools::check_process_running($p)) {
				$finish_worker->($p);
			    }
			}
			sleep(1);
		    }
		}
		while (scalar(keys %$workers)) {
		    for my $p (keys %$workers) {
			if (!PVE::ProcFSTools::check_process_running($p)) {
			    $finish_worker->($p);
			}
		    }
		    sleep(1);
		}
	    }

	    syslog('info', "all VMs suspended");

	    return;
	};

	return $rpcenv->fork_worker('suspendall', undef, $authuser, $code);
    }});


my $create_migrate_worker = sub {
    my ($nodename, $type, $vmid, $target, $with_local_disks) = @_;

    my $upid;
    if ($type eq 'lxc') {
	my $online = PVE::LXC::check_running($vmid) ? 1 : 0;
	print STDERR "Migrating CT $vmid\n";
	$upid = PVE::API2::LXC->migrate_vm(
	   { node => $nodename, vmid => $vmid, target => $target, restart => $online });
    } elsif ($type eq 'qemu') {
	print STDERR "Check VM $vmid: ";
	*STDERR->flush();
	my $online = PVE::QemuServer::check_running($vmid, 1) ? 1 : 0;
	my $preconditions = PVE::API2::Qemu->migrate_vm_precondition(
	    {node => $nodename, vmid => $vmid, target => $target});
	my $invalidConditions = '';
	if ($online && !$with_local_disks && scalar @{$preconditions->{local_disks}}) {
	    $invalidConditions .= "\n  Has local disks: ";
	    $invalidConditions .= join(', ', map { $_->{volid} } @{$preconditions->{local_disks}});
	}

	if (@{$preconditions->{local_resources}}) {
	    $invalidConditions .= "\n  Has local resources: ";
	    $invalidConditions .= join(', ', @{$preconditions->{local_resources}});
	}

	if ($invalidConditions && $invalidConditions ne '') {
	    print STDERR "skip VM $vmid - precondition check failed:";
	    die "$invalidConditions\n";
	}
	print STDERR "precondition check passed\n";
	print STDERR "Migrating VM $vmid\n";

	my $params = {
	    node => $nodename,
	    vmid => $vmid,
	    target => $target,
	    online => $online,
	};
	$params->{'with-local-disks'} = $with_local_disks if defined($with_local_disks);

	$upid = PVE::API2::Qemu->migrate_vm($params);
    } else {
	die "unknown VM type '$type'\n";
    }

    my $task = PVE::Tools::upid_decode($upid);

    return $task->{pid};
};

__PACKAGE__->register_method ({
    name => 'migrateall',
    path => 'migrateall',
    method => 'POST',
    proxyto => 'node',
    protected => 1,
    permissions => {
	description => "The 'VM.Migrate' permission is required on '/' or on '/vms/<ID>' for each "
	    ."ID passed via the 'vms' parameter.",
	user => 'all',
    },
    description => "Migrate all VMs and Containers.",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    target => get_standard_option('pve-node', { description => "Target node." }),
	    maxworkers => {
		description => "Maximal number of parallel migration job. If not set, uses"
		    ."'max_workers' from datacenter.cfg. One of both must be set!",
		optional => 1,
		type => 'integer',
		minimum => 1
	    },
	    vms => {
		description => "Only consider Guests with these IDs.",
		type => 'string',  format => 'pve-vmid-list',
		optional => 1,
	    },
	    "with-local-disks" => {
		type => 'boolean',
		description => "Enable live storage migration for local disk",
		optional => 1,
	    },
	},
    },
    returns => {
	type => 'string',
    },
    code => sub {
	my ($param) = @_;

	my $rpcenv = PVE::RPCEnvironment::get();
	my $authuser = $rpcenv->get_user();

	if (!$rpcenv->check($authuser, "/", [ 'VM.Migrate' ], 1)) {
	    my @vms = PVE::Tools::split_list($param->{vms});
	    if (scalar(@vms) > 0) {
		$rpcenv->check($authuser, "/vms/$_", [ 'VM.Migrate' ]) for @vms;
	    } else {
		raise_perm_exc("/, VM.Migrate");
	    }
	}

	my $nodename = $param->{node};
	$nodename = PVE::INotify::nodename() if $nodename eq 'localhost';

	my $target = $param->{target};
	my $with_local_disks = $param->{'with-local-disks'};
	raise_param_exc({ target => "target is local node."}) if $target eq $nodename;

	PVE::Cluster::check_cfs_quorum();

	PVE::Cluster::check_node_exists($target);

	my $datacenterconfig = cfs_read_file('datacenter.cfg');
	# prefer parameter over datacenter cfg settings
	my $maxWorkers = $param->{maxworkers} || $datacenterconfig->{max_workers} ||
	    die "either 'maxworkers' parameter or max_workers in datacenter.cfg must be set!\n";

	my $code = sub {
	    $rpcenv->{type} = 'priv'; # to start tasks in background

	    my $vmlist = &$get_filtered_vmlist($nodename, $param->{vms}, 1, 1);
	    if (!scalar(keys %$vmlist)) {
		warn "no virtual guests matched, nothing to do..\n";
		return;
	    }

	    my $workers = {};
	    my $workers_started = 0;
	    foreach my $vmid (sort keys %$vmlist) {
		my $d = $vmlist->{$vmid};
		my $pid;
		eval { $pid = &$create_migrate_worker($nodename, $d->{type}, $vmid, $target, $with_local_disks); };
		warn $@ if $@;
		next if !$pid;

		$workers_started++;
		$workers->{$pid} = 1;
		while (scalar(keys %$workers) >= $maxWorkers) {
		    foreach my $p (keys %$workers) {
			if (!PVE::ProcFSTools::check_process_running($p)) {
			    delete $workers->{$p};
			}
		    }
		    sleep(1);
		}
	    }
	    while (scalar(keys %$workers)) {
		foreach my $p (keys %$workers) {
		    # FIXME: what about PID re-use ?!?!
		    if (!PVE::ProcFSTools::check_process_running($p)) {
			delete $workers->{$p};
		    }
		}
		sleep(1);
	    }
	    if ($workers_started <= 0) {
		die "no migrations worker started...\n";
	    }
	    print STDERR "All jobs finished, used $workers_started workers in total.\n";
	    return;
	};

	return $rpcenv->fork_worker('migrateall', undef, $authuser, $code);

    }});

__PACKAGE__->register_method ({
    name => 'get_etc_hosts',
    path => 'hosts',
    method => 'GET',
    proxyto => 'node',
    protected => 1,
    permissions => {
	check => ['perm', '/', [ 'Sys.Audit' ]],
    },
    description => "Get the content of /etc/hosts.",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	},
    },
    returns => {
	type => 'object',
	properties => {
	    digest => get_standard_option('pve-config-digest'),
	    data => {
		type => 'string',
		description => 'The content of /etc/hosts.'
	    },
	},
    },
    code => sub {
	my ($param) = @_;

	return PVE::INotify::read_file('etchosts');

    }});

__PACKAGE__->register_method ({
    name => 'write_etc_hosts',
    path => 'hosts',
    method => 'POST',
    proxyto => 'node',
    protected => 1,
    permissions => {
	check => ['perm', '/nodes/{node}', [ 'Sys.Modify' ]],
    },
    description => "Write /etc/hosts.",
    parameters => {
	additionalProperties => 0,
	properties => {
	    node => get_standard_option('pve-node'),
	    digest => get_standard_option('pve-config-digest'),
	    data => {
		type => 'string',
		description =>  'The target content of /etc/hosts.'
	    },
	},
    },
    returns => {
	type => 'null',
    },
    code => sub {
	my ($param) = @_;

	PVE::Tools::lock_file('/var/lock/pve-etchosts.lck', undef, sub {
	    if ($param->{digest}) {
		my $hosts = PVE::INotify::read_file('etchosts');
		PVE::Tools::assert_if_modified($hosts->{digest}, $param->{digest});
	    }
	    PVE::INotify::write_file('etchosts', $param->{data});
	});
	die $@ if $@;

	return;
    }});

# bash completion helper

sub complete_templet_repo {
    my ($cmdname, $pname, $cvalue) = @_;

    my $repo = PVE::APLInfo::load_data();
    my $res = [];
    foreach my $templ (keys %{$repo->{all}}) {
	next if $templ !~ m/^$cvalue/;
	push @$res, $templ;
    }

    return $res;
}

package PVE::API2::Nodes;

use strict;
use warnings;

use PVE::SafeSyslog;
use PVE::Cluster;
use PVE::RESTHandler;
use PVE::RPCEnvironment;
use PVE::API2Tools;
use PVE::JSONSchema qw(get_standard_option);

use base qw(PVE::RESTHandler);

__PACKAGE__->register_method ({
    subclass => "PVE::API2::Nodes::Nodeinfo",
    path => '{node}',
});

__PACKAGE__->register_method ({
    name => 'index',
    path => '',
    method => 'GET',
    permissions => { user => 'all' },
    description => "Cluster node index.",
    parameters => {
	additionalProperties => 0,
	properties => {},
    },
    returns => {
	type => 'array',
	items => {
	    type => "object",
	    properties => {
		node => get_standard_option('pve-node'),
		status => {
		    description => "Node status.",
		    type => 'string',
		    enum => ['unknown', 'online', 'offline'],
		},
		cpu => {
		    description => "CPU utilization.",
		    type => 'number',
		    optional => 1,
		    renderer => 'fraction_as_percentage',
		},
		maxcpu => {
		    description => "Number of available CPUs.",
		    type => 'integer',
		    optional => 1,
		},
		mem => {
		    description => "Used memory in bytes.",
		    type => 'integer',
		    optional => 1,
		    renderer => 'bytes',
		},
		maxmem => {
		    description => "Number of available memory in bytes.",
		    type => 'integer',
		    optional => 1,
		    renderer => 'bytes',
		},
		level => {
		    description => "Support level.",
		    type => 'string',
		    optional => 1,
		},
		uptime => {
		    description => "Node uptime in seconds.",
		    type => 'integer',
		    optional => 1,
		    renderer => 'duration',
		},
		ssl_fingerprint => {
		    description => "The SSL fingerprint for the node certificate.",
		    type => 'string',
		    optional => 1,
		},
	    },
	},
	links => [ { rel => 'child', href => "{node}" } ],
    },
    code => sub {
	my ($param) = @_;

	my $rpcenv = PVE::RPCEnvironment::get();
	my $authuser = $rpcenv->get_user();

	my $clinfo = PVE::Cluster::get_clinfo();
	my $res = [];

	my $nodelist = PVE::Cluster::get_nodelist();
	my $members = PVE::Cluster::get_members();
	my $rrd = PVE::Cluster::rrd_dump();

	foreach my $node (@$nodelist) {
	    my $can_audit = $rpcenv->check($authuser, "/nodes/$node", [ 'Sys.Audit' ], 1);
	    my $entry = PVE::API2Tools::extract_node_stats($node, $members, $rrd, !$can_audit);

	    $entry->{ssl_fingerprint} = eval { PVE::Cluster::get_node_fingerprint($node) };
	    warn "$@" if $@;

	    push @$res, $entry;
	}

	return $res;
    }});

1;
