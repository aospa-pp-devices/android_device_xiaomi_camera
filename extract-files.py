#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import shutil

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

namespace_imports = []

def lib_fixup_campostproc_system_suffix(lib: str, partition: str, *args, **kwargs):
    return f'{lib}_system' if partition == 'system' else None

def replace_with_shim_impl(ctx, file, file_path, *args, **kwargs):
    # The 5.x camera's libgui blob is A13-built and references
    # android::binder::atrace_begin/end, symbols A17's libbinder no longer
    # exports.  Ship the A15-era libgui (which calls the atrace_*_body
    # functions in libcutils instead) as a shim in its place.
    shutil.copyfile(f'{ctx.module_dir}/shim/libgui-xiaomi.so', file_path)

lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
    (
        'vendor.xiaomi.hardware.campostproc@1.0',
    ): lib_fixup_campostproc_system_suffix,
}

blob_fixups: blob_fixups_user_type = {
    'system/lib64/libgui-xiaomi.so': blob_fixup()
        .call(replace_with_shim_impl)
        .replace_needed(
            'android.hardware.graphics.common-V4-ndk.so',
            'android.hardware.graphics.common-V7-ndk.so',
        ),
    (
        'system/lib64/libcamera_algoup_jni.xiaomi.so',
        'system/lib64/libcamera_mianode_jni.xiaomi.so',
    ): blob_fixup()
        .replace_needed(
            'libgui.so',
            'libgui-xiaomi.so',
        ),
    'system/priv-app/MiuiCamera/MiuiCamera.apk': blob_fixup(),
}

module = ExtractUtilsModule(
    'camera',
    'xiaomi',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
