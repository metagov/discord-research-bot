from core.extension import Extension
from models.channel import Channel
from discord.ext import commands
import discord


class Bridge(Extension):
    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        if not message.author.bot:
            for channel in await self.get_adjacent_channels(message):
                await self.replicate(channel, message)

    async def get_adjacent_channels(self, message) -> None:
        channels = []

        channel_document = Channel.record(message.channel)
        if channel_document.group:

            # Find other documents in same group.
            adjacent_documents = Channel.objects(
                group=channel_document.group,
                id__ne=channel_document.id,
            )

            for adjacent_document in adjacent_documents:
                try:
                    channel = await adjacent_document.fetch(self.bot)
                    channels.append(channel)
                except Exception as exception:
                    # Document will be deleted, so just pass on it.
                    pass

        return channels

    async def replicate(self, channel: discord.TextChannel, message) -> None:
        # try:
        #     webhook = await channel.create_webhook(name=message.author.name)
        # except discord.errors.HTTPException: # max webhooks
        #     print("clearing webhooks")
        #     hooks = await channel.webhooks()
        #     for h in hooks:
        #         await h.delete()
        
        webhook = await channel.create_webhook(name=message.author.name)

        await webhook.send(
            content=message.content,
            embeds=message.embeds,
            avatar_url=message.author.avatar_url,
            # TODO: Figure out how to send attachments as well.
        )

        await webhook.delete()

    # Public
    # ======

    def set_channel_group(self, channel, group) -> None:
        channel_document = Channel.record(channel)
        channel_document.group = group
        channel_document.save()

    def reset_channel_group(self, channel) -> None:
        channel_document = Channel.record(channel)
        channel_document.group = None
        channel_document.save()

    # Commands
    # ========

    @commands.command()
    @commands.is_owner()
    async def sgroup(self, ctx, *, group: str) -> None:
        self.set_channel_group(ctx.channel, group)
        await ctx.send('Done!')


def setup(bot) -> None:
    cog = Bridge(bot)
    bot.add_cog(cog)
