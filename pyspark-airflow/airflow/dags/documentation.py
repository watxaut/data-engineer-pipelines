d_extracts = {
    'orders': 'Extracts orders from microservice and lands the information in bronze schema in DL',
    'customer_courier_chat_messages': 'Extracts customer_courier_chat_messages from microservice and lands the '
                                      'information in bronze schema in DL',
}

transformation = 'Performs some window functions on messages tables to get first message, second message ' \
                 'and last order stage, then aggregates messages per order_id and the left joins orders with ' \
                 'messages, so we have all orders with their messages (if any) in gold/customer_courier_conversations' \
                 'table'
