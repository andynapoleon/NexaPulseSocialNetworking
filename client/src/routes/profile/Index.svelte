<script>
  import ProfilePosts from "../../widgets/ProfilePosts.svelte";
  import ProfileWidget from "./ProfileWidget.svelte";
  import { onMount } from "svelte";
  import {
    authToken,
    isLoginPage,
    getCurrentUser,
    server,
    refreshToken,
  } from "../../stores/stores.js";
  import { navigate } from "svelte-routing"; // Assuming you're using svelte-routing for navigation
  import { get } from "svelte/store";
  import { fetchWithRefresh } from "../../utils/apiUtils.js";

  let fullName = "";
  let github = "";
  let email = "";
  let userId = "";
  let profileImage = "";
  let host = "";

  let isAuthenticated = false;
  export let params;

  onMount(async () => {
    isAuthenticated = $authToken !== "";
    if (!isAuthenticated) {
      $isLoginPage = true;
      navigate("/");
    }
    // get the id from the URL
    const path = window.location.pathname;
    const pathSegments = path.split("/");
    console.log(pathSegments);
    userId = pathSegments[pathSegments.length - 1];
    // if the user is looking at their on profile
    if (userId == getCurrentUser().userId) {
      fullName = getCurrentUser().name;
      github = getCurrentUser().github;
      email = getCurrentUser().email;
      profileImage = getCurrentUser().profileImage;
      host = getCurrentUser().host;
    } else {
      userId = pathSegments.pop();
      console.log(`${userId}`);
      const profileEndpoint = server + `/api/profile/${userId}`;
      const response = await fetch(profileEndpoint, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${get(authToken)}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch profile");
      }
      const data = await response.json();
      fullName = data.full_name;
      github = data.github;
      email = data.email;
      profileImage = data.profileImage;
      host = data.host;
    }
  });
</script>

<main class="main">
  <div class="profile-layout">
    <div class="profile-widget">
      <ProfileWidget
        profileImage={profileImage}
        name={fullName}
        {email}
        {github}
        {userId}
        {host}
      />
    </div>
    <div class="posts">
      <ProfilePosts authorId={params.id} />
    </div>
  </div>
</main>

<style>
  .main {
    padding-top: 180px;
    padding-left: 350px;
    padding-right: 150px;
  }

  .profile-layout {
    display: flex;
    justify-content: space-between;
    
    gap: 5rem; /* Adjust the gap as needed */
  }

  .profile-widget {
    flex: 1; /* Adjust the flex basis as needed */
    max-width: 350px; /* Adjust the width as needed */
  }

  .posts {
    flex: 3; /* Adjust the flex basis as needed */
  }
</style>
