# Variables that define how we connect to the storage cluster or vserver
ce_cluster              = "cluster_or_vserver_mgmt_interface_dns_name"
ce_port                 = "443"
ce_user                 = "devops"
ce_passwd               = "devops123"
ce_vserver              = "vserver_name"
ce_transport            = "HTTPS"
ce_style                = "LOGIN"
ce_server_type          = "FILER"
ce_ontapi_major_version = "1"
ce_ontapi_minor_version = "31"

# Variables related to volume creation
ce_volume_create_options = {}
ce_volume_create_options['containing-aggr-name']        = 'aggr1_svlngen4_c01_nas_03_1'
ce_volume_create_options['size']                        = '10240g'
ce_volume_create_options['unix-permissions']            = '777'
ce_volume_create_options['export-policy']               = 'codeeasy'
ce_volume_create_options['snapshot-policy']             = 'none'
ce_volume_create_options['percentage-snapshot-reserve'] = '0'
ce_volume_create_options['user-id']                     = '0'
ce_volume_create_options['group-id']                    = '25'
ce_volume_create_options['space-reserve']               = 'none'
ce_volume_create_options['efficiency-policy']           = 'AlwaysOn'
ce_volume_create_options['volume-security-style']       = 'unix'

# Options maxfiles setting
ce_vol_maxfiles         = "75000000"
