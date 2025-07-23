import { rtmClient, channel, addBotMessageToDom, displayName } from './room2_rtc.js';

export function setupRTM() {
    console.log("Setting up RTM functionality...");
    
    const messageForm = document.getElementById('message__form');
    if (messageForm) {
        messageForm.addEventListener('submit', sendMessage);
    }
    
    window.addEventListener('beforeunload', leaveChannel);
    
    if (channel) {
        channel.on('MemberJoined', handleMemberJoined);
        channel.on('MemberLeft', handleMemberLeft);
        channel.on('ChannelMessage', handleChannelMessage);
    }
}

export let handleMemberJoined = async (MemberId) => {
    console.log('A new member has joined the room:', MemberId);
    addMemberToDom(MemberId);

    let members = await channel.getMembers();
    updateMemberTotal(members);

    let {name} = await rtmClient.getUserAttributesByKeys(MemberId, ['name']);
    addBotMessageToDom(`Witaj na zajęciach ${name}! 👋`);
}

export let addMemberToDom = async (MemberId) => {
    let {name} = await rtmClient.getUserAttributesByKeys(MemberId, ['name'])

    let membersWrapper = document.getElementById('member__list')
    let memberItem = `<div class="member__wrapper" id="member__${MemberId}__wrapper">
                        <span class="green__icon"></span>
                        <p class="member_name">${name}</p>
                    </div>`

    membersWrapper.insertAdjacentHTML('beforeend', memberItem)
}

export let updateMemberTotal = async (members) => {
    let total = document.getElementById('members__count')
    total.innerText = members.length
}

export let handleMemberLeft = async (MemberId) => {
    removeMemberFromDom(MemberId)

    let members = await channel.getMembers()
    updateMemberTotal(members)
}

export let removeMemberFromDom = async (MemberId) => {
    let memberWrapper = document.getElementById(`member__${MemberId}__wrapper`)
    let name = memberWrapper.getElementsByClassName('member_name')[0].textContent
    addBotMessageToDom(`${name} opuścił/a zajęcia.`)

    memberWrapper.remove()
}

export let getMembers = async () => {
    let members = await channel.getMembers();
    updateMemberTotal(members);
    for (let i = 0; members.length > i; i++){
        addMemberToDom(members[i]);
    }
    return members;
}

export let handleChannelMessage = async (messageData, MemberId) => {
    console.log('A new message was received')
    let data = JSON.parse(messageData.text)

    if(data.type === 'chat'){
        addMessageToDom(data.displayName, data.message)
    }
}

export let sendMessage = async (e) => {
    e.preventDefault()

    let message = e.target.message.value
    channel.sendMessage({text:JSON.stringify({'type':'chat', 'message':message, 'displayName':displayName})})
    addMessageToDom(displayName, message)
    e.target.reset()
}

export let addMessageToDom = (name, message) => {
    let messagesWrapper = document.getElementById('messages')

    function convertLinksToAnchors(text) {
        const urlPattern = /(\bhttps?:\/\/[^\s<]+[^\s]*|www\.[^\s<]+[^\s]*)/gi;
        return text.replace(urlPattern, function(url) {
            var fullUrl = url;
            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                fullUrl = 'http://' + url;
            }
            return `<a href="${fullUrl}" target="_blank">${url}</a>`;
        });
    }

    let messageWithLinks = convertLinksToAnchors(message);

    let newMessage = `<div class="message__wrapper">
                        <div class="message__body">
                            <strong class="message__author">${name}</strong>
                            <p class="message__text">${messageWithLinks}</p>
                        </div>
                    </div>`

    messagesWrapper.insertAdjacentHTML('beforeend', newMessage)

    let lastMessage = document.querySelector('#messages .message__wrapper:last-child')
    if(lastMessage){
        lastMessage.scrollIntoView()
    }
}


export let leaveChannel = async () => {
    if (channel) {
        await channel.leave();
    }
    if (rtmClient) {
        await rtmClient.logout();
    }
}
