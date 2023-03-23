import smartpy as sp

class Lottery(sp.Contract):
    def __init__(self,_admin):
        self.init(
            players = sp.map(l={}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost = sp.tez(1),
            tickets_available = sp.nat(6),
            starting_tickets = sp.nat(6),
            max_tickets = sp.nat(5),
            admin = _admin,
        )
    
    @sp.entry_point
    def buy_ticket(self, num_tickets):
        sp.set_type(num_tickets, sp.TNat)

        # Sanity checks
        sp.verify(self.data.tickets_available >= num_tickets, "NO TICKETS AVAILABLE")
        sp.verify(sp.amount >= self.data.ticket_cost, "INVALID AMOUNT")
        

        # Storage updates
        sp.for i in sp.range(0, num_tickets):
            self.data.players[sp.len(self.data.players)] = sp.sender
        self.data.tickets_available = sp.as_nat(self.data.tickets_available - num_tickets)

        # Return extra tez balance to the sender
        extra_balance = sp.amount - sp.mul(self.data.ticket_cost, num_tickets)
        sp.if extra_balance > sp.mutez(0):
            sp.send(sp.sender, extra_balance)

    @sp.entry_point
    def change_ticket_cost(self, new_cost):
        
        sp.set_type(new_cost, sp.TMutez)

        # Sanity checks 
        sp.verify(self.data.tickets_available == self.data.starting_tickets, "GAME HAS ALREADY STARTED")
        sp.verify(new_cost != self.data.ticket_cost, "NO CHANGE IN COST")

        self.data.ticket_cost = new_cost

    @sp.entry_point
    def change_max_tickets(self, new_max):
        
        sp.set_type(new_max, sp.TNat)

        # Sanity checks 
        sp.verify(self.data.tickets_available == self.data.starting_tickets, "GAME HAS ALREADY STARTED")
        sp.verify(new_max != self.data.max_tickets, "NO CHANGE IN MAX TICKETS")

        self.data.max_tickets = new_max       
    
    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)

        # Sanity checks
        sp.verify(sp.sender == self.data.admin, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == 0, "GAME IS YET TO END")

        # Pick a winner
        winner_id = random_number % self.data.max_tickets
        winner_address = self.data.players[winner_id]

        # Send the reward to the winner
        sp.send(winner_address, sp.balance)

        # Reset the game
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

    @sp.entry_point
    def default(self):
        sp.failwith("NOT ALLOWED")

@sp.add_test(name = "main")
def test():
    scenario = sp.test_scenario()

    # Test accounts
    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    mike = sp.test_account("mike")

    # Contract instance
    lottery = Lottery(admin.address)
    scenario += lottery

    # change_ticket_values
    scenario.h2("change_ticket_cost (valid test)")
    scenario += lottery.change_ticket_cost(sp.tez(2))

    scenario.h2("change_max_tickets (valid test)")
    scenario += lottery.change_max_tickets(3)
    # buy_ticket
    scenario.h2("buy_ticket (valid test)")
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(4), sender = alice)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(2), sender = bob)
    scenario += lottery.buy_ticket(3).run(amount = sp.tez(6), sender = mike)

    scenario.h2("change_ticket_cost (failure test)")
    scenario += lottery.change_ticket_cost(sp.tez(1)).run(valid = False)

    scenario.h2("change_max_tickets (failure test)")
    scenario += lottery.change_max_tickets(5).run(valid = False)

    scenario.h2("buy_ticket (failure test)")
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(2), sender = alice, valid = False)

    # end_game
    scenario.h2("end_game (valid test)")
    scenario += lottery.end_game(21).run(sender = admin)