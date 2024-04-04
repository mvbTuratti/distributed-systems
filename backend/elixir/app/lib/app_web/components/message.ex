defmodule AppWeb.Message do
  use Phoenix.Component
@doc """
  Renders a message.

  ## Examples

      <.message user="User" sender={@sender} hash={@hash} status={@status} ></.message>
  """
  attr :sender, :boolean, default: true
  attr :user, :string, default: ""
  attr :hash, :string, required: true
  attr :status, :boolean, default: false
  attr :timestamp, :string, default: DateTime.utc_now() |> DateTime.add(-3, :hour) |> DateTime.to_string() |> String.split(".") |> List.first()
  attr :message, :string, required: true
  attr :last, :boolean, default: true
  attr :first, :boolean, default: false


  def message(assigns) do
    ~H"""
    <div class={[
      "chat",
      @sender && "chat-end",
      not @sender && "chat-start"
    ]}
    id={"#{@hash}"}>
      <div :if={@first} class="chat-header">
          <span :if={not @sender}><%= @user %></span>
          <time class="text-xs opacity-50"><%= @timestamp %></time>
      </div>
      <div class={[
        "chat-bubble",
        @sender && "chat-bubble-info",
        not @sender && "chat-bubble-accent"
       ]}>
        <%= @message %>
      </div>
      <div :if={@last and @sender} class="chat-footer opacity-50"><%= if @status, do: 'Delivered', else: 'Sending...' %></div>
  </div>
  """
  end
end
