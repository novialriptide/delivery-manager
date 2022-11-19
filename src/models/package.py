class Package:
    def __init__(
        self,
        cost,
        delivery_fee,
        destination_node,
        is_fragile=False,
        max_dist=-1,
    ):
        self.cost = cost
        self.delivery_fee = delivery_fee
        self.destination_node = destination_node
        self.is_fragile = is_fragile
        self.max_dist = max_dist
        self.health = 100

    def __str__(self):
        special_tags = []
        if self.is_fragile:
            special_tags.append("FRAGILE")
        if self.max_dist != -1:
            special_tags.append(f"MAX_DISTANCE: {self.max_dist}m")

        special_tags = ", ".join(special_tags)
        return f"<Package Cost: ${self.cost}, Delivery Fee: ${self.delivery_fee}, Specials: [{special_tags}]>"
