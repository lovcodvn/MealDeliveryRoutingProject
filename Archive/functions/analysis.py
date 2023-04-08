import matplotlib.pyplot as plt
from classes.deliveryrouting import DeliveryRouting

def orders_list(dr: DeliveryRouting, final_result, orders, locations, file_name, instance_dir):
    print('Number of orders:', len(dr.orders))
    print('Number of orders in horizon list:', sum([len(v) for v in dr.orders_by_horizon_interval.values()]))
    orders_in_initilization = 0
    for t in final_result:
        for res in final_result[t]:
            for ro in res:
                orders_in_initilization+=len(ro.bundle)
    print('Number of orders in initilization', orders_in_initilization)

    print('order horizon by len of restaurant having orders')
    d = {k:len(v) for k,v in final_result.items()}
    d = {k:v for k,v in sorted(d.items(), key = lambda x: x[1], reverse=True)}
    print(d)

    t = 575
    orders_list = [o.id for o in dr.orders_by_horizon_interval[t]]
    print(orders_list)

    print(orders[(orders['ready_time']<t+10) & (orders['placement_time']<t) & (orders['placement_time']>=t-5)].sort_values(by=['ready_time']))

    print(orders[orders['order'].isin(orders_list)].sort_values(by=['ready_time']))

    print(final_result[t])

    for res in final_result[t]:
        for ro in res:
            print(ro.restaurant_id,[o.id for o in ro.bundle])

    # find route has two orders:
    for t in final_result:
        for res in final_result[t]:
            for ro in res:
                if len(ro.bundle)>1:
                    print(t, ro.restaurant_id,[o.id for o in ro.bundle])

    # Plot chart
    x = [locations.at['r1','x'],locations.at['o237','x'],locations.at['o215','x']]
    y = [locations.at['r1','y'],locations.at['o237','y'],locations.at['o215','y']]
    lable = ['r1','o237','o215']
    for i, txt in enumerate(lable):
        plt.annotate(txt, (x[i], y[i]))
    plt.scatter(x, y)
    
    plt.savefig('./{}/{}-scatter.png'.format(instance_dir, file_name))
    plt.close()

    return None
