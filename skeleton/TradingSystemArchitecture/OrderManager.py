from necessary_import import *;

class OrderManager():
    def __init__ (self, context):
        self.context = context
        self.instruments = dict()
        
        # used to manage expected orders, making sure cash is freed by closing positions
        # before opening any new orders if necessary
        self.order_queue_open = dict()
        self.order_queue_close = dict()
        return
    
    def add_instruments(self, values):
        self.instruments = combine_dicts(self.instruments,
                                         values,
                                         op=operator.add)
        return
    
    def send_order_through(self, instrument, nb_shares=0, style=MarketOrder()):
        '''
        MarketOrder()
        LimitOrder()
        '''
        order(instrument, nb_shares, style=style)
        return
        
    def add_percent_orders(self, data, input_dict):
        # get current positions percentage of portfolio
        # to determine is the input_dict percentage of a position
        # corresponds to selling or buying said position
        self.update_current_positions(data)
        
        # distribute new percentage according to current position percentage
        for position in input_dict:
            if input_dict[position] > self.current_positions[position]:
                self.order_queue_open = combine_dicts({position:input_dict[position]},
                                         self.order_queue_open,
                                         op=operator.add)
            else:
                self.order_queue_close = combine_dicts({position:input_dict[position]},
                                         self.order_queue_close,
                                         op=operator.add)
        return
    
    def exit_positions (self):
        if len(self.order_queue_close)<1:
            return
            
        for k in self.order_queue_close:
            order_target_percent(k, self.order_queue_close[k])
            
        self.order_queue_close = dict()
        return
        
    def enter_positions(self):
        '''
            Objective: Prevent "not enough funds available"
                
            we do not buy new positions if:
                (1) no orders, 
                (2) need to sell some and free some cash, 
                (3) some new positions are not yet filled and unfilled positions may free some cash
    
        
            Consideration: 
            this logic does not work on daily data (because of the pending 'closing transactions'
            the objective is to have a daily mode that is as close as possible to a minute mode            
            Consequently:
            >> daily mode: should allow every orders at once as all orders will be submitted at same time (EOD closing)
            >> minute mode: first close orders (sell long and close shorts), then move to buy more of current positions
        ''' 
        data_freq = get_environment(field='data_frequency')
        if data_freq == 'minute' and (len(self.order_queue_open) <1 or len(self.order_queue_close)>1 or len(get_open_orders()) > 0):
            if len(self.order_queue_close)>1:
                msg = "long position status: wait to fill all position_exit"
                print(msg)
            elif len(get_open_orders()) > 0:
                msg = "long positions status: waiting for unfilled orders to get through"
                print(msg)
            return
            
        for k in self.order_queue_open:
            order_target_percent(k, self.order_queue_open[k])
            
        self.order_queue_open = dict()
        return
        
    def update (self):
        self.exit_positions()
        self.enter_positions()
        return

    def update_current_positions(self, data):
        self.current_positions = dict()
        for k in self.instruments.values():
                self.current_positions[k] = (data[k].price*self.context.portfolio.positions[k].amount) / self.context.portfolio.portfolio_value
        return 