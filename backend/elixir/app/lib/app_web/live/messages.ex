defmodule AppWeb.Messages do
  use AppWeb, :live_view
  import AppWeb.AmqpListener, only: [add_client: 1, remove_client: 1]

  @exchange "message"

  @impl true
  def mount(_, _session, socket) do
    {channel, connection} = set_amqp_publisher()
    if connected?(socket), do:
      add_client_to_mailing_messages(), else: IO.puts("client not yet connected")

    {:ok, assign(socket, client_name: create_client_name(), message: "",
      messages: [], amqp_conn: connection, amqp_channel: channel)}
  end
  @impl true
  def terminate(_, _) do
    remove_client(self())
  end

  @impl true
  def handle_event("message", %{"key" => "Enter", "value" => value}, socket) do
    socket = add_user_message(socket, value) |> assign(message: "")
    # IO.inspect(socket)
    {:noreply, push_event(socket, "reset-message", %{})}
  end
  def handle_event("message", _, socket), do: {:noreply, socket}

  @impl true
  def handle_info({:message, payload}, socket) do
    IO.puts("message received!")
    IO.inspect(payload)
    {:noreply, update_message_status(socket, payload)}
  end

  def update_message_status(%{assigns: %{client_name: name}} = socket, %{"name" => name} = message) do
    updated_messages = Enum.map(socket.assigns.messages, fn msg ->
      if msg[:hash] == message["hash"], do: %{msg | status: true} , else: msg
    end)
    assign(socket, messages: updated_messages)
  end

  def update_message_status(socket, message) do
    {user, new_message} = shape_message_received(message, socket)
    messages = update_previous_message(user, socket)
    assign(socket, messages: [ new_message | messages ])
  end
  defp shape_message_received(%{"name" => user, "content" => msg, "hash" => hash, "timestamp" => timestamp}, socket) do
    {user,
    %{user: user, message: msg, hash: hash,
    timestamp: timestamp, sender: false, last: true, status: true, first: is_first_received_user_msg?(socket, user)}}
  end
  def create_client_name() do
    adjectives = ["adorable", "bubbly", "crazy", "dizzy", "energetic", "fluffy", "giggly", "happy", "jolly", "kooky", "loopy", "merry", "nutty", "playful", "quirky", "silly", "twinkly", "wacky", "zany"]
    nouns = ["apple", "banana", "cookie", "donut", "elephant", "flamingo", "giraffe", "hedgehog", "iguana", "jellyfish", "koala", "lemur", "monkey", "narwhal", "octopus", "penguin", "quokka", "rhinoceros", "sloth", "toucan", "unicorn", "vampire", "walrus", "x-ray fish", "yeti", "zebra"]
    connectors = [" ", "-", ".", "-"]
    Enum.reduce([adjectives, connectors, nouns], "",fn options, name ->
      [word] = Enum.take_random(options, 1)
      name <> word
    end) <> " Elixir " <> "#{inspect self()}"
  end

  def set_amqp_publisher() do
    {:ok, connection} = AMQP.Connection.open
    {:ok, channel} = AMQP.Channel.open(connection)
    AMQP.Exchange.declare(channel, @exchange, :fanout)
    # AMQP.Queue.declare(channel, "messages")
    {channel, connection}
  end
  def send_message_to_amqp(message, channel) do
    message = %{"name" => message[:user], "content" => message[:message], "hash" => message[:hash],
    "timestamp" => message[:timestamp]}
    # AMQP.Basic.publish(channel, "", "messages", Jason.encode!(message))
    AMQP.Basic.publish(channel, @exchange, "", Jason.encode!(message))
  end

  def timestamp() do
    DateTime.utc_now() |> DateTime.add(-3, :hour) |> DateTime.to_string() |> String.split(".") |> List.first()
  end

  defp add_client_to_mailing_messages() do
    add_client(self())
  end

  defp add_user_message(socket, message) do
    new_message = create_sender_message(socket, message)
    socket = update_last_status(socket)
    send_message_to_amqp(new_message, socket.assigns.amqp_channel)
    assign(socket, messages: [ new_message | socket.assigns.messages])
  end
  defp create_sender_message(%{assigns: %{client_name: user}} = socket, message) do
    %{user: user, hash: create_hash(15), sender: true,
    last: true, first: is_first_message_of_user?(socket),
    timestamp: timestamp(), status: false, message: message}
  end
  defp create_hash(bytes_count) do
    bytes_count
    |> :crypto.strong_rand_bytes()
    |> Base.url_encode64(padding: false)
  end
  defp is_first_message_of_user?(%{assigns: %{messages: []}}), do: true
  defp is_first_message_of_user?(%{assigns: %{client_name: user, messages: [ %{user: user} | _]}}), do: false
  defp is_first_message_of_user?(_), do: true

  defp is_first_received_user_msg?(%{assigns: %{messages: []}}, _), do: true
  defp is_first_received_user_msg?(%{assigns: %{messages: [ %{user: user}]}}, user), do: false
  defp is_first_received_user_msg?(_, _), do: true

  defp update_last_status(%{assigns: %{client_name: user, messages: [ %{user: user, last: true} = msg | remainder]}} = socket) do
    assign(socket, messages: [ %{msg | last: false} | remainder])
  end
  defp update_last_status(socket), do: socket

  defp update_previous_message(user, %{assigns: %{messages: [ %{user: user, last: true} = msg | remainder]}}) do
    [%{msg | last: false}| remainder]
  end
  defp update_previous_message(_, %{assigns: %{messages: msgs}}), do: msgs
end
