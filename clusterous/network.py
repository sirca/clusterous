import boto.ec2
import boto.vpc            

class NetSetup(object):
    """
    """
    def __init__(self, cluster_name, vpc_conn, ec2_conn, region, vpc_id = None):
        self.cluster_name = cluster_name
        self.vpc_conn = vpc_conn
        self.ec2_conn = ec2_conn
        self.default_zone = 'a'
        self.availability_zone = region + self.default_zone
        self.vpc = self.get_set_vpc(vpc_id)
        
    def tag_resource(self, name_name):
        return {'Name': self.cluster_name + '-'+str(name_name), 'Project': self.cluster_name}
    
    def get_set_vpc(self, vpc_id = None):
        vpc = None

        if vpc_id is None:
            vpc_name_full = "{0}-vpc".format(self.cluster_name)
            
            # Get list of VPCs
            vpcs = self.vpc_conn.get_all_vpcs()
            for i in vpcs:
                if i.tags.get('Name','') == vpc_name_full:
                    vpc = i
        
            if vpc is None:
                # Create VPC
                vpc = self.vpc_conn.create_vpc('10.2.0.0/16')
                vpc.add_tags({'Name': vpc_name_full})
                self.vpc_conn.modify_vpc_attribute(vpc.id, enable_dns_support=True)
                self.vpc_conn.modify_vpc_attribute(vpc.id, enable_dns_hostnames=True)
        
                # Create network acl
                network_acl = self.vpc_conn.create_network_acl(vpc.id)
                network_acl.add_tags({'Name': self.cluster_name + '-acl'})
        else:
            vpc = self.vpc_conn.get_all_vpcs(vpc_ids=[vpc_id])[0]
    
        return vpc
    
    def get_set_private_sg(self, sg_name):
        security_group = None
        security_group_name_full = "{0}-{1}".format(self.cluster_name, sg_name)
        security_groups = self.vpc_conn.get_all_security_groups()
        for i in security_groups:
            if i.tags.get('Name','') == security_group_name_full:
                security_group = i
    
        if security_group is None:
            # Private Security group
            security_group = self.vpc_conn.create_security_group(self.cluster_name+"-{0}".format(sg_name), 'Private security group for ' + self.cluster_name, self.vpc.id)
            security_group.add_tags(self.tag_resource(sg_name))
            security_group.authorize(ip_protocol='-1', from_port=0, to_port=65535, cidr_ip='0.0.0.0/0')
        
        return security_group

    def get_set_public_sg(self, sg_name):
        security_group = None
        security_group_name_full = "{0}-{1}".format(self.cluster_name, sg_name)
        security_groups = self.vpc_conn.get_all_security_groups()
        for i in security_groups:
            if i.tags.get('Name','') == security_group_name_full:
                security_group = i
    
        if security_group is None:
            # Public Security group
            private_security_group = self.get_set_private_sg("private-sg")
            security_group = self.vpc_conn.create_security_group(self.cluster_name+"-{0}".format(sg_name), 'Public security group for ' + self.cluster_name, self.vpc.id)
            security_group.add_tags(self.tag_resource(sg_name))
            security_group.authorize(ip_protocol='tcp', from_port=22, to_port=22, cidr_ip='0.0.0.0/0')
            security_group.authorize(ip_protocol='tcp', from_port=22000, to_port=22000, cidr_ip='0.0.0.0/0')
            security_group.authorize(ip_protocol='-1', from_port=0, to_port=65535, src_group=private_security_group)
        
        return security_group
    
    def get_set_subnet(self, subnet_name):
        subnet = None
        subnet_name_full = "{0}-{1}-{2}".format(self.cluster_name, subnet_name, self.default_zone)
        # Get list of subnets
        subnets = self.vpc_conn.get_all_subnets(filters={'vpcId':self.vpc.id, 'availabilityZone':self.availability_zone})
        max_subnet_cidr = 1
        if subnets:
            for i in subnets:
                if i.tags.get('Name','') == subnet_name_full:
                    subnet = i
                else:
                    subnet_cidr = i.cidr_block.split('.')
                    if int(subnet_cidr[2]) > max_subnet_cidr:
                        max_subnet_cidr = int(subnet_cidr[2])
    
        if subnet is None:
            vpc_cidr = self.vpc.cidr_block.split('.')
            cidr = '{0}.{1}.{2}.0/24'.format(vpc_cidr[0], vpc_cidr[1], max_subnet_cidr + 1)
            subnet = self.vpc_conn.create_subnet(self.vpc.id, cidr, availability_zone=self.availability_zone)
            subnet.add_tags(self.tag_resource("{0}-{1}".format(subnet_name, self.default_zone)))
    
        return subnet
    
    def get_set_gateway(self, gateway_name):
        gateway = None
        gateway_name_full = "{0}-{1}".format(self.cluster_name, gateway_name)
        # Get list of gateways
        gateways = self.vpc_conn.get_all_internet_gateways()
        for i in gateways:
            if i.tags.get('Name','') == gateway_name_full:
                gateway = i
    
        if gateway is None:
            # Create a internet gateway
            gateway = self.vpc_conn.create_internet_gateway()
            gateway.add_tags(self.tag_resource(gateway_name))
            self.vpc_conn.attach_internet_gateway(gateway.id, self.vpc.id)
    
        return gateway
    
    def get_set_route_table(self, route_table_name):
        route_table = None
        route_table_name_full = "{0}-{1}".format(self.cluster_name, route_table_name)
        # Get list of route tables
        route_tables = self.vpc_conn.get_all_route_tables(filters={'vpc_id':self.vpc.id})
        for i in route_tables:
            if i.tags.get('Name','') == route_table_name_full:
                route_table = i

        if route_table is None:
            # Create a Route Table
            route_table = self.vpc_conn.create_route_table(self.vpc.id)
            route_table.add_tags(self.tag_resource(route_table_name))
    
        return route_table
    
    def link_publi_subnet_to_gateway(self):
        gateway = self.get_set_gateway('gateway')
        public_subnet = self.get_set_subnet('public-subnet')
        route_table = self.get_set_route_table('public-route-table')
        
        # Connect public subnet to the gateway
        self.vpc_conn.create_route(route_table.id, destination_cidr_block="0.0.0.0/0", gateway_id=gateway.id)
        self.vpc_conn.associate_route_table(route_table.id, public_subnet.id)
        
        return True

    def link_private_subnet_to_nat(self, nat_instance_id):
        private_route_table = self.get_set_route_table('private-route-table')
        private_subnet = self.get_set_subnet('private-subnet')
        
        # Connect private subnet to the nat instance
        self.vpc_conn.create_route(private_route_table.id, destination_cidr_block="0.0.0.0/0", instance_id=nat_instance_id)
        self.vpc_conn.associate_route_table(private_route_table.id, private_subnet.id)
        
        return True
    
    def create_nat_instance(self, instance_name, keypair_name, nat_ami_image, instance_type):
        public_subnet = self.get_set_subnet('public-subnet')
        public_security_group = self.get_set_public_sg("public-sg")
        interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(subnet_id=public_subnet.id,
            groups=[public_security_group.id, ], associate_public_ip_address=True)
        interfaces = boto.ec2.networkinterface.NetworkInterfaceCollection(interface)
        reservation = self.ec2_conn.run_instances(nat_ami_image, key_name=keypair_name, instance_type=instance_type, network_interfaces=interfaces)
        
        nat_instance = reservation.instances[0]
        nat_instance.add_tags(self.tag_resource(instance_name))
        
        return nat_instance
    
    def create_controller_instance(self, instance_name, keypair_name, controller_ami_image, instance_type):
        private_subnet = self.get_set_subnet('private-subnet')
        private_security_group = self.get_set_private_sg("private-sg")
        interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(subnet_id=private_subnet.id,
            groups=[private_security_group.id, ], associate_public_ip_address=False)
        interfaces = boto.ec2.networkinterface.NetworkInterfaceCollection(interface)
        reservation = self.ec2_conn.run_instances(controller_ami_image, key_name=keypair_name, instance_type=instance_type, network_interfaces=interfaces)
    
        controller_instance = reservation.instances[0]
        controller_instance.add_tags(self.tag_resource(instance_name))
        
        return controller_instance
