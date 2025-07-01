package com.fitu.fitu.domain.user.controller;

import com.fitu.fitu.domain.user.dto.request.ProfileRequest;
import com.fitu.fitu.domain.user.dto.response.BodyImageAnalysisResponse;
import com.fitu.fitu.domain.user.dto.response.ProfileResponse;
import com.fitu.fitu.domain.user.entity.User;
import com.fitu.fitu.domain.user.service.UserService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RequiredArgsConstructor
@RequestMapping("/user")
@RestController
public class UserController {

    private final UserService userService;

    @PostMapping("/profile")
    public ProfileResponse registerProfile(@Valid @RequestBody final ProfileRequest requestDto) {
        final User user = userService.registerProfile(requestDto);

        return ProfileResponse.of(user);
    }

    @GetMapping("/profile")
    public ProfileResponse getProfile(@RequestHeader("Fitu-User-UUID") final String userId) {
        final User user = userService.getProfile(userId);

        return ProfileResponse.of(user);
    }

    @PatchMapping("/profile")
    public ProfileResponse updateProfile(@RequestHeader("Fitu-User-UUID") final String userId,
                                         @Valid @RequestBody final ProfileRequest requestDto) {
        final User user = userService.updateProfile(userId, requestDto);

        return ProfileResponse.of(user);
    }

    @PostMapping(value = "/profile/image-analysis", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public BodyImageAnalysisResponse analyzeBodyImage(@RequestPart(value = "bodyImage") final MultipartFile file) {
         return userService.analyzeBodyImage(file);
    }
}