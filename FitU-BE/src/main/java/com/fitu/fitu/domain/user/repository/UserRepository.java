package com.fitu.fitu.domain.user.repository;

import com.fitu.fitu.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<User, String> {
}