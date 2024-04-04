defmodule AppWeb.AmqpListener do
  use GenServer
  use AMQP

  def start_link(_) do
    GenServer.start_link(__MODULE__, [], name: Listener)
  end

  @exchange    "gen_server_test_exchange"
  @queue       "messages"
  @queue_error "#{@queue}_error"

  def init(_opts) do
    {:ok, conn} = Connection.open()
    {:ok, chan} = Channel.open(conn)
    setup_queue(chan)

    # Limit unacknowledged messages to 10
    :ok = Basic.qos(chan, prefetch_count: 20)
    # Register the GenServer process as a consumer
    {:ok, _consumer_tag} = Basic.consume(chan, @queue)
    {:ok, %{channel: chan, messages: [], clients: []}}
  end

  # Confirmation sent by the broker after registering this process as a consumer
  def handle_info({:basic_consume_ok, %{consumer_tag: _consumer_tag}}, state) do
    {:noreply, state}
  end

  # Sent by the broker when the consumer is unexpectedly cancelled (such as after a queue deletion)
  def handle_info({:basic_cancel, %{consumer_tag: _consumer_tag}}, state) do
    {:stop, :normal, state}
  end

  # Confirmation sent by the broker to the consumer process after a Basic.cancel
  def handle_info({:basic_cancel_ok, %{consumer_tag: _consumer_tag}}, state) do
    {:noreply, state}
  end

  def handle_info({:basic_deliver, payload, %{delivery_tag: tag, redelivered: redelivered}}, %{channel: chan, messages: msg} = state) do
    # You might want to run payload consumption in separate Tasks in production
    payload = consume(chan, tag, redelivered, payload)
    state = %{state | messages: [ payload | msg ] |> Enum.take(30) }
    IO.puts("handling message from queue")
    IO.inspect(state[:clients])

    state[:clients]
      |> Enum.map(fn client_pid -> Task.async(fn -> Process.send(client_pid, {:message, payload}, []) end) end)
      |> Enum.map(&Task.await/1)
    {:noreply, state}
  end

  def handle_call({:add_client, pid}, _ , state) do
    IO.puts("adding client")
    IO.inspect(pid)
    state = %{state | clients: [pid | state[:clients]] }
    {:reply, :ok, state}
  end
  def handle_call({:remove_client, pid}, _ , state) do
    IO.puts("removing client")
    IO.inspect(pid)
    state = %{state | clients: Enum.filter(state[:clients], fn e -> e !== pid end) }
    {:reply, :ok, state}
  end

  defp setup_queue(chan) do
    {:ok, _} = Queue.declare(chan, @queue_error)
    # Messages that cannot be delivered to any consumer in the main queue will be routed to the error queue
    {:ok, _} = Queue.declare(chan, @queue)
    :ok = Exchange.fanout(chan, @exchange)
    :ok = Queue.bind(chan, @queue, @exchange)
  end

  defp consume(channel, tag, redelivered, payload) do

    :ok = Basic.ack channel, tag
    Jason.decode!(payload)

  rescue
    # Requeue unless it's a redelivered message.
    # This means we will retry consuming a message once in case of exception
    # before we give up and have it moved to the error queue
    #
    # You might also want to catch :exit signal in production code.
    # Make sure you call ack, nack or reject otherwise consumer will stop
    # receiving messages.
    _exception ->
      :ok = Basic.reject channel, tag, requeue: not redelivered
      IO.puts "Error converting #{payload} to a map"
  end

  def add_client(client_pid), do: GenServer.call(Listener, {:add_client, client_pid})
  def remove_client(client_pid), do: GenServer.call(Listener, {:remove_client, client_pid})

end
